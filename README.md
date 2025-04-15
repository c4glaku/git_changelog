# Git Changelog Generator

Git Changelog Generator is an AI-powered command-line tool that generates a user-friendly changelog based on Git commit history.

## Installation
After cloning the repository, install the project and its dependencies via pip. The required packages are listed in requirements.txt. Run the following command in the root directory of the repository:
`pip instal -e .`

## Setup
Before running the tool, create a .env file in the root directory and add your OpenAI API key:
`OPENAI_API_KEY=your_openai_key_here`

## Usage
To generate a changelog for the last, for example, 10 commits and print to the console:
`python changelog.py 10`

To generate a changelog and save it to CHANGELOG.md:
`python changelog.py 10 --output CHANGELOG.md`

##### Note: Only works in directories with an initiated git repository.

## Requirements
- Git installed and accesible in PATH
- Python 3.8+