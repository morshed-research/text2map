import json

"""
Load needed Files
"""
# ------------------------------------------------------------------------------
with open('../data/buildings_metadata.json', 'r') as file:
    buildings_metadata = json.load(file)

with open('../data/text2map_navigation_instructions.json', 'r') as file:
    text2map_navigation_instructions = json.load(file)

with open('../data/regions_labels.json', 'r') as file:
    regions_lables = json.load(file)
# ------------------------------------------------------------------------------


def generate_prompt(building_id, instruction_index, chatgpt_format=True):
    introduction_str = (
        "Act as a computer scientist cartographer and create a map "
        "representation of an indoor building. I will provide you with 3 "
        "things. First, the expected output format. Second, information about "
        "the room-like regions of the building. We might have regions that "
        "have the same name/label. Third, instructions for an agent to navigate "
        "through the building. The navigation instructions are independent of "
        "each other and they are not ordered. Also, please only focus on the "
        "room-like regions of the building, and don't include any information "
        "about the objects in it.\n\n"
    )

    introduction_str = "Create a connectivity Matrix from the following navigation instructions"
    
    output_format_str = (
        "OUTPUT FORMAT: Return only a JSON object, I don't want any other "
        "comments. The JSON contains one key named connectivity_graph which has "
        "a value of a Python Dictionary. The dictionary contains a key for each "
        "region index and the value for each key is a list of indices of regions "
        "that are connected to it.\n\n"
    )
    
    # Add Information about metadata of of the building
    building_information = buildings_metadata[building_id]
    number_of_levels = len(building_information)
    regions_information_str = (
        f"ROOM-LIKE REGIONS INFORMATION: This building contains {number_of_levels} "
        "Levels.\n"
    )
    
    # Loop through levels and add their information
    for i in range(number_of_levels):
        regions_information_str += (
            f"Level {i} contains {len(building_information[str(i)])} regions:\n"
        )
        # Add regions in level i
        for region_idx in building_information[str(i)]['regions']:
            regions_information_str += (
                f"- Region {region_idx} is a {regions_lables[building_information[str(i)]['regions'][region_idx]]}.\n"
            )
        regions_information_str += '\n'

    # Add Navigation Instructions
    building_navigation_instructions = text2map_navigation_instructions[building_id]
    navigation_instructions = building_navigation_instructions[instruction_index]
    
    # navigation_instructions = navigation_instructions[:int(len(navigation_instructions) * 0.1)]
    
    navigation_instructions_str = "NAVIGATION INSTRUCTIONS:\n"
    i = 1
    for instruction in navigation_instructions:
        start_region = instruction['start_region']
        navigation_instructions_str += (
            f"- Instruction {i}: "
            f"You are in region {start_region}. "
            f"- {instruction['instruction'][1]}\n"
        )
        if instruction['end_region'] != '-1':
            end_region = instruction['end_region']
            navigation_instructions_str += f"You have arrived to region {end_region}."
        navigation_instructions_str += "\n"
        i +=1

    # Combine everything together
    if chatgpt_format:
        return introduction_str, output_format_str + navigation_instructions_str
        # return introduction_str, output_format_str + regions_information_str + navigation_instructions_str
    
    prompt = introduction_str + output_format_str + regions_information_str + navigation_instructions_str
    return prompt