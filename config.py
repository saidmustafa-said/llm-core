# config.py

from llamaapi import LlamaAPI
from dotenv import load_dotenv
import os

# Define the root directory
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
print(ROOT_DIR)

# Define the path to the CSV file
TAGS_LIST = os.path.join(ROOT_DIR, "data", "tags.csv")
CATEGORY_SUBCATEGORY_LIST = os.path.join(
    ROOT_DIR, "data", "category_subcategory.csv")
DATASET = os.path.join(ROOT_DIR, "data", "dataset.csv")


# Initialize the LlamaAPI SDK
load_dotenv()
api_key = os.getenv("apiKey")


LLAMA_API = LlamaAPI(api_key)
