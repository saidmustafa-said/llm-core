# config.py

from llamaapi import LlamaAPI
from dotenv import load_dotenv
import os

# Define the root directory
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


# Define the path to the CSV file
TAGS_LIST = os.path.join(ROOT_DIR, "data", "tags.csv")
DATASET = os.path.join(ROOT_DIR, "data", "filtered_tags.csv")


# Initialize the LlamaAPI SDK
load_dotenv()
api_key = os.getenv("apiKey")

LLAMA_API = LlamaAPI(api_key)



