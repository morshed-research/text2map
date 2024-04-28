def pretty_print_building_instructions(building_info_dict):
    i = 1
    for instruction in building_info_dict['instructions']['instructions']:
        print(f'Instructions sequence {i}')
        print(f'1. {instruction[0]}')
        print(f'2. {instruction[1]}')
        print(f'3. {instruction[2]}')
        print('\n---------------------')
        i += 1

def combine_buildings_dicts(dict_1, dict_2):
    keys = set(list(dict_1.keys()) +  list(dict_2.keys()))
    
    combined_dict = {}
    for key in keys:
        if key in dict_1:
            if key in dict_2:
                combined_dict[key] = {
                    'occurs': dict_1[key]['occurs'] + dict_2[key]['occurs'],
                    'viewpoints': dict_1[key]['viewpoints'] | dict_2[key]['viewpoints'],
                    'instructions': dict_1[key]['instructions'] + dict_2[key]['instructions'] 
                }
            else:
                combined_dict[key] = dict_1[key]
        else:
            combined_dict[key] = dict_2[key]

    return combined_dict