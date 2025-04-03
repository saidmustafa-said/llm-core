import json
import os


def save_args_to_json(filename, **kwargs):
    """
    Takes any number of keyword arguments, converts them into a JSON object,
    and saves them to a file called 'tempshold.json'. If the file does not exist,
    it is created.
    """

    # Load existing data if the file exists
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    # Update the existing data with new arguments
    existing_data.update(kwargs)

    # Save the updated data back to the file
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(existing_data, file, indent=4)

    print(f"Data saved to {filename}")


def extract_json():
    """
    Reads and returns the JSON content of 'tempshold.json' as a JSON string.
    """
    filename = "tempshold.json"

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                return json.dumps(data, indent=4)
            except json.JSONDecodeError:
                return "{}"
    return "{}"


# # Example usage
# save_args_to_json(name="Alice", age=30, city="New York")
# json_output = extract_json()
# print(json_output)
