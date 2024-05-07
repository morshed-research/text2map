import sys
sys.path.append('../')

from tqdm import tqdm
from config import CHATGPT_API
from prompting_engine.prompter import generate_prompt
from metrics import edges_similarity, approx_ged

import csv
import json
import pickle
import random
from openai import OpenAI

client = OpenAI()

    
def prompt_chatgpt(instructions: dict, num_shots, model: str = CHATGPT_API.MODEL,
        seed: int =CHATGPT_API.SEED, save_path: str = ''):
    """
    This funtions calls prompts chatgpt api. 

    Args:
        instructions (dict): 
            Prompts for few-shot learning. 
            format: {
                'system': str, 
                'shots': [{'user': str, 'assistant': str}],
                'prompt': str
            }.
            pre-condition: len(instructions) == num_shots+1.

        num_shots (int): Number of training shots.
        model (str, optional): ChatGPT modelto prompt.
        seed (int, optional): Model seed. Defaults to CHATGPT_API.SEED.
        save_path (int, optional): .pkl file to save the returned object. Deafaults to ".
    """
    print('Model:', model)
    print('Seed:', seed)
    system = {'role': 'system', 'content': instructions['system']}

    # Few-Shot learning
    shots = []
    for i in range(num_shots):
        user_i = {'role': 'user', 'content': instructions['shots'][i]['user']}
        assistant_i = {'role': 'assistant', 'content': instructions['shots'][i]['assistant']}
        shots.append(user_i)
        shots.append(assistant_i)

    prompt = {'role': 'user', 'content': instructions['prompt']}

    completion = client.chat.completions.create(
        model=model,
        seed = seed,
        response_format={"type": "json_object"},
        messages=[system, *shots, prompt]
    )

    # Save Result
    if save_path:
        with open(save_path, 'wb') as pickle_file:
            pickle.dump(completion, pickle_file)

    return completion


def test_pipeline(text2map_instructions_path, regions_connectivity_path, 
    num_shots, save_path=''):
    """
    Prompts all instructions to chatgpt and gets reults. The first num_shots 
    building are used for few-shot learning. 
    Pre-condition: len(text2map_instructions) > num_shots.

    Args:
        text2map_instructions_path (str.json): Path to the generated instructions.
        regions_connectivity_path (str): Path to the ground-truth connectivity.
        num_shots (int): Number of shots in few-shots learning.
        save_path (str, optional): .pkl file to save returned objects. Defaults to ''.

    Returns:
        list(completion): List of completions returned by chatgpt.
    """
    # Open file to load instructions and ground-truth connectivity graphs
    with open(text2map_instructions_path, 'r') as file:
        text2map_instructions = json.load(file)
    with open(regions_connectivity_path, 'rb') as file:
        regions_connectivity = pickle.load(file)

    buildings = list(text2map_instructions.keys())

    # Loops through the building and prompt GPT
    results = {}

    for i in tqdm(range(0, len(text2map_instructions))):
        print('Building:', buildings[i])

        # Prepare the shots
        shots_buildings = random.sample(buildings, num_shots)
        shots = []
        for building in shots_buildings:
            system, user = generate_prompt(building, 0)
            assistant = json.dumps({'connectivity_graph': regions_connectivity[building]})
            shots.append({'user': user, 'assistant': assistant})

        # Build prompt
        results[buildings[i]] = []
        for j in range(len(text2map_instructions[buildings[i]])):
            system, user = generate_prompt(buildings[i], j)
            prompt = {'system': system, 'shots': shots, 'prompt': user}
            chatgpt_result = prompt_chatgpt(prompt, num_shots)
            results[buildings[i]].append(chatgpt_result)

        # Save Result
        if save_path:
            with open(save_path, 'wb') as pickle_file:
                pickle.dump(results, pickle_file)

            print(f'Saved building {i}')

    # Save Result
    if save_path:
        with open(save_path, 'wb') as pickle_file:
            pickle.dump(results, pickle_file)

    return results


def compare_results(chatgpt_results_path, regions_connectivity_path, save_path=''):
    # Open file to load chatgpt results and ground-truth connectivity graphs
    with open(chatgpt_results_path, 'rb') as file:
        chatgpt_results = pickle.load(file)
    with open(regions_connectivity_path, 'rb') as file:
        regions_connectivity = pickle.load(file)

    # Loop over chatgpt results and convert them into code
    sims = []
    for building in chatgpt_results:
        ground_truth = regions_connectivity[building]
    
        min_dist = 1000
        max_sim = 0
        for result in chatgpt_results[building]:
            try:
                chatgpt_result = json.loads(result.choices[0].message.content)
                graph_dist = approx_ged(ground_truth, chatgpt_result['connectivity_graph'])
                _, graph_sim = edges_similarity(ground_truth, chatgpt_result['connectivity_graph'])
                if graph_dist < min_dist:
                    min_dist = graph_dist
                if graph_sim > max_sim:
                    max_sim = graph_sim
            except Exception as e:
                print(e)
                continue
        
        sims.append([building, len(ground_truth), min_dist, max_sim])

        print(f'{building}: {min_dist}')
        print(f'{building}: {max_sim}')
    
    # Save file as csv
    if save_path:
        with open(save_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Building ID", "Number of Regions", "Similarity 1", "Similarity 2"])
            # Writing data
            for row in sims:
                writer.writerow(row)

    return sims