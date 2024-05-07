# Text2map
From Navigational Instructions to Graph-Based Indoor Map Representations Using LLMs

![text2map solution](<figures/text2map.png>)

# Research Paper
WIP
# Getting Started
- Clone the repo
- Python version 3.11.4
- Install requirements
    - ```pip install -r requirements.txt```
- To regenerate the data, make sure to get [Mattterport3D](https://niessner.github.io/Matterport/) and [R2R](https://bringmeaspoon.org/) datasets 

# Directory Structure
- README.md
- LICENSE
- requirements.txt
- config.py -- Parameters configurations
- utils.py -- General utility functions
- prompting_engine
    - prompter.py -- Pipline to generate a final prompt
- graph_generator
    - chatgpt_api.py -- Pipline to call OpenAI's LLMs and Evaluate the responses
    - metrics.py -- Metrics used in the evaluation process
- anaylsis
    - matterport3d_analysis.py -- Extracts and analyse data from Matterport3D
    - r2r_analysis.py -- Extracts and analyse data from Matterport3D
- data -- Files of data used in the research project
- figures