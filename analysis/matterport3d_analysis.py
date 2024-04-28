import os
import json
import pickle


def buildings_viewpoints_to_regions(dataset_dir, save_path=''):
    """
    Parses information about the regions in every building from .house files
    and panorama_to_regions files, and returns viewpoint_to_region dictionary.
    
    Args:
        dataset_dir (str): path to house_segmentations directories of matterport3d.
        save_path (str.json, optional): Path to save result. Defaults to ''.

    Return:
        dict: {
            building_id (str): {
                "regions_num": int,
                "viewpoint_to_region": {
                    viewpoint_id (str): int (region index),
                    ...
                }
            },
            ...
        }
    """
    result = {}
    # Loop through the buildings directories
    for building in os.listdir(dataset_dir):
        building_path = os.path.join(dataset_dir, building)
        if os.path.isdir(building_path):
            
            # Read numbers of regions from .house file
            with open(f'{building_path}/house_segmentations/{building}.house', 'r') as file:
                # Second line contains building's metadata
                for i in range(2):
                    line = file.readline()

                # Add number of regions to the results dictionary
                line_list = line.strip().split()
                result[building] = {
                    'regions_num': int(line_list[10]),
                    'viewpoint_to_region': {}
                }

            # Read numbers of regions from .house file
            with open(f'{building_path}/house_segmentations/panorama_to_region.txt', 'r') as file:
                # Loop through the lines of viewpoints
                line = file.readline()
                while line:
                    # Parse the line, and add it to result dict
                    line_list = line.strip().split()
                    result[building]['viewpoint_to_region'][line_list[1]] = int(line_list[2])
                    line = file.readline()
    
    # Save file
    if save_path:
        with open(save_path, 'w') as json_file:
            json.dump(result, json_file)

    return result


def buildings_metadata(dataset_dir, save_path=''):
    """
    Parses .house file for each building and returns metadata about the levels,
    and the regions that belong to that building.

    Args:
        dataset_dir (str): path to house_segmentations directories of matterport3d.
        save_path (str.json, optional): Path to save result. Defaults to ''.

    Returns:
        dict: {
            building_id (str): {
                level_index (int): {
                    "label": str (one letter label),
                    "regions": {
                        region_index (int): str (one letter label),
                        ...
                    },
                    ...
                }
            },
            ...
        }
    """
    result = {}
    # Loop through the buildings directories
    for building in os.listdir(dataset_dir):
        result[building] = {}

        building_path = os.path.join(dataset_dir, building)
        if os.path.isdir(building_path):

            # Read numbers of regions from .house file
            with open(f'{building_path}/house_segmentations/{building}.house', 'r') as file:
                # Second line contains building's metadata
                for i in range(2):
                    line = file.readline()
                
                line_list = line.strip().split()
                num_levels = int(line_list[12])
                num_regions = int(line_list[10])

                # Levels information
                for i in range(num_levels):
                    line = file.readline()
                    line_list = line.strip().split()
                    level_index = int(line_list[1])
                    level_label = line_list[3]
                    result[building][level_index] = {'label': level_label, 'regions': {}}

                # Regions information
                for i in range(num_regions):
                    line = file.readline()
                    line_list = line.strip().split()
                    region_index = int(line_list[1])
                    level_index = int(line_list[2])
                    region_label = line_list[5]
                    result[building][level_index]['regions'][region_index] = region_label 
    
    # Save file
    if save_path:
        with open(save_path, 'w') as json_file:
            json.dump(result, json_file)

    return result


def build_regions_connectivity(scans_file, connectivity_dir, viewpoints_to_regions_path, save_path=''):
    """
    builds connectivit graphs of regions withing each building.

    Args:
        scans_file (str.txt): File that contains buildings name in new lines.
        connectivity_dir (str): Path to directory of Matterport3d connectivities.
        viewpoints_to_regions_path (str.json): Path to the dict.
        save_path (str.pkl, optional): Path to save result. Defaults to ''.

    Returns:
        dict: {
            building_id (str): {
                region_id (int): set(connected regions),
                 ...
            },
            ...
        }
    """
    # Load the viewpoint_to_region
    with open(viewpoints_to_regions_path, 'r') as file:
        viewpoint_to_region = json.load(file)

    # Get all buildings IDs
    building_ids = []
    with open(scans_file, 'r') as file:
        for line in file:
            building_ids.append(line.strip())

    # Loop through the 
    connectivity_dict = {}
    for id in building_ids:
        # Open connectivity file of building id
        connectivity_dict[id] = {}
        with open(f'{connectivity_dir}/{id}_connectivity.json', 'r') as file:
            viewpoints = json.load(file)
        
        # Loop through connectivity of viewpoints
        for viewpoint in viewpoints:
            unobstructed = viewpoint['unobstructed']
            region = viewpoint_to_region[id]['viewpoint_to_region'][viewpoint['image_id']]
            
            if region != -1:
                # Get list of unobstructed regions from viewpoint
                unobstructed_regions = []
                for i in range(len(unobstructed)):
                    if unobstructed[i]:
                        region_i = viewpoint_to_region[id]['viewpoint_to_region'][viewpoints[i]['image_id']]
                        if region_i != -1:
                            unobstructed_regions.append(region_i)
                
                # Add connections to connectivity dictionary
                unobstructed_regions = set(unobstructed_regions)
                if region in connectivity_dict[id]:
                    connectivity_dict[id][region].update(unobstructed_regions)
                else:
                    connectivity_dict[id][region] = unobstructed_regions

        # Convert sets to list
        for region in connectivity_dict[id]:
            connectivity_dict[id][region] = list(connectivity_dict[id][region])

    # Save file
    if save_path:
        with open(save_path, 'wb') as pickle_file:
            pickle.dump(connectivity_dict, pickle_file)

    return connectivity_dict


def remove_uncovered_regions_from_metadata(metadata_path, 
    viewpoints_to_regions_path, save_path = ""):
    # Load connectivity_graphs viewpoint_to_region
    with open(metadata_path, 'r') as file:
        metadata = json.load(file)
    with open(viewpoints_to_regions_path, 'r') as file:
        viewpoint_to_region = json.load(file)

    # loop through the buildings
    new_metadata = {}
    for building_id in metadata:

        # collect the covered regions
        covered_regions = set()
        for viewpoint in viewpoint_to_region[building_id]["viewpoint_to_region"]:
            covered_regions.add(viewpoint_to_region[building_id]["viewpoint_to_region"][viewpoint])

        # remove uncovered regions
        new_building_metadata = {}
        for level in metadata[building_id]:
            
            # add covered regions
            new_building_metadata[level] = {"label": metadata[building_id][level]["label"], "regions": {}}
            for region in metadata[building_id][level]["regions"]:
                if int(region) in covered_regions:
                    new_building_metadata[level]["regions"][region] = metadata[building_id][level]["regions"][region]

            if len(new_building_metadata[level]) == 0:
                del new_building_metadata[level]

        new_metadata[building_id] = new_building_metadata

    # Save file
    if save_path:
        with open(save_path, 'w') as json_file:
            json.dump(new_metadata, json_file)

    return new_metadata