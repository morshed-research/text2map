import csv
import json
import pickle
import itertools
from tqdm import tqdm


def build_buildings_to_instructions_and_viewpoints(json_file):
    """
    Loops over instructions, and collects information about the buildings.

    Args:
        json_file (str): instructions file.

    Returns:
        dict: {
            building_id (str): {
                'occurs': int (Number of instructions about this building),
                'viewpoints': set() (Set of unique viewpoints covered by instructions of the building),
                'instructions': [{path_id, int, path: [], instructions: []}] (All instructions in this building)
            },
            ...
        }
    """
    buildings_dict = {}

    # Open the file for reading
    with open(json_file, 'r') as file:
        data = json.load(file)
    
    for entry in data:
        buildings_dict.setdefault(
            entry['scan'], 
            {'occurs': 0, 'viewpoints': set(), 'instructions': []}
        )
        # count the number of occurrences of each building
        buildings_dict[entry['scan']]['occurs'] += 1
        # count the number of uniqe viewpoints per building
        buildings_dict[entry['scan']]['viewpoints'] |= set(entry['path'])
        # add instructions
        instructions = {'path_id': entry['path_id'],'path': entry['path'], 'instructions': entry['instructions']}
        buildings_dict[entry['scan']]['instructions'].append(instructions)

    return buildings_dict


def map_coverage_per_building(buildings_to_instructions_and_viewpoints_path, viewpoints_to_regions_path):
    # Load files
    with open(buildings_to_instructions_and_viewpoints_path, 'rb') as file:
        buildings_to_instructions_and_viewpoints = pickle.load(file)
    with open(viewpoints_to_regions_path, 'r') as file:
        viewpoints_to_regions = json.load(file)

    # Loop over buildings
    result = {}
    for building in buildings_to_instructions_and_viewpoints:
        covered_regions = set()
       
        # Loop over viewpoints in r2r
        for viewpoint in buildings_to_instructions_and_viewpoints[building]['viewpoints']:
            covered_regions.add(viewpoints_to_regions[building]['viewpoint_to_region'][viewpoint])
        covered_regions.discard(-1)

        # Add Coverage to result dict  
        result[building] = [len(covered_regions), viewpoints_to_regions[building]['regions_num']]

    return result


def map_coverage_per_building_csv(map_coverage_per_building_dict):
    # Prepare data for CSV
    csv_data = []
    for building, values in map_coverage_per_building_dict.items():
        all_regions = values[1]
        regions_covered = values[0]
        coverage_percentage = (regions_covered / all_regions) * 100 if all_regions > 0 else 0
        csv_data.append([building, all_regions, regions_covered, coverage_percentage])

    # File path for the CSV
    file_path = 'output.csv'

    # Write to CSV
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)

        # Write the header
        writer.writerow(['Building', '# All Regions', '# Regions Covered by R2R', 'Coverage Percentage'])

        # Write the data
        writer.writerows(csv_data)


def build_region_to_instructions(r2r_informbuildings_to_instructionsation_path,
                                  viewpoints_to_regions_path, save_path=''):
    """
    Returns a dictionary that contains each navigation sequences divided into 
    regions, for every building in the dataset.

    Args:
        r2r_informbuildings_to_instructionsation_path (str): Path to pkl file storing r2r analysis. 
        viewpoints_to_regions_path (str): Path to json file.

    Returns:
        dict: {
            building_id (str): {
                region (str): [                
                    {
                        'path_id': str,
                        'start_region': int,
                        'end_region': int,
                        'instructions': [str]         
                    },
                    ...
                ],
                ...
            },
            ...
        }
    """
   # Load files
    with open(r2r_informbuildings_to_instructionsation_path, 'rb') as file:
        r2r_informbuildings_to_instructionsation = pickle.load(file)
    with open(viewpoints_to_regions_path, 'r') as file:
        viewpoints_to_regions = json.load(file)

    # Loop through the instructions of the building
    result = {}
    for building in r2r_informbuildings_to_instructionsation:
        result[building] = {}
        for instruction in r2r_informbuildings_to_instructionsation[building]['instructions']:
            
            # Get starting and ending regions of the paths
            start_viewpoint = instruction['path'][0]
            start_region = viewpoints_to_regions[building]['viewpoint_to_region'][start_viewpoint]
            if len(instruction['path'][0]) == 1:
                end_region = -1
            else:
                end_viewpoint = instruction['path'][-1]
                end_region = viewpoints_to_regions[building]['viewpoint_to_region'][end_viewpoint]

            # Loop through viewpoints and add instructions to regions
            for viewpoint in instruction['path']:
                region = viewpoints_to_regions[building]['viewpoint_to_region'][viewpoint]
                if  region in result[building]:
                    result[building][region].append({
                        'path_id': instruction['path_id'], 
                        'start_region': start_region,
                        'end_region': end_region,
                        'instruction' :instruction['instructions']
                    })
                else:
                    result[building][region] = [{
                        'path_id': instruction['path_id'],
                        'start_region': start_region,
                        'end_region': end_region,
                        'instruction' :instruction['instructions']
                    }]

    # Save file
    if save_path:
        with open(save_path, 'wb') as pickle_file:
            pickle.dump(result, pickle_file)

    return result


def create_region_based_instructions_combinations(regions_to_instructions,
    num_seqs_per_building, save_path=''):
    """
    Generates combinations of navigation instructions for each building, such
    that each region in the building is covered at least once, and max number of
    instructions in each combination equal to the number of regions.

    Args:
        regions_to_instructions (_type_): _description_

    Returns:
        dict: {
            building_id (str): [
                [
                    {
                        'path_id': str,
                        'start_region': int,
                        'end_region': int,
                        'instructions': [str, str, str]
                    },
                    ... 
                ],
                ...
            ],
            ...
        }
    """
    # Load files
    with open(regions_to_instructions, 'rb') as file:
        building_data = pickle.load(file)
        
    # Dictionary to store the final result
    result = {}

    # Iterate over each building in the data with tqdm for progress tracking
    for building_id in tqdm(building_data, desc="Processing buildings"):
        result[building_id] = []
        regions = building_data[building_id]

        # Extract lists of instructions for each region in the current building
        region_instructions = [region for region in regions.values()]

        # Generate all possible combinations of instructions, one from each region
        combinations = itertools.product(*region_instructions)

        count = 0
        unique_combinations = []
        for combination in combinations:
            if count >= num_seqs_per_building:
                break

            # Remove duplicates
            seen_path_ids = set()
            new_comb = []

            for d in combination:
                if d['path_id'] not in seen_path_ids:
                    new_comb.append(d)
                    seen_path_ids.add(d['path_id'])

            if seen_path_ids not in unique_combinations:
                # Convert the unique tuples back into lists
                result[building_id].append(new_comb)
                unique_combinations.append(seen_path_ids)
                count +=1

    if save_path:
        with open(save_path, 'w') as file:
            json.dump(result, file)

    return result