# import json


# def sort_and_save_json(json_file):
#     # Load the JSON data
#     with open(json_file, 'r', encoding='utf-8') as file:
#         data = json.load(file)

#     # Sort the JSON: keys alphabetically and values (lists) sorted
#     sorted_data = {k: sorted(v) for k, v in sorted(data.items())}

#     # Save the sorted data back to the JSON file
#     with open(json_file, 'w', encoding='utf-8') as file:
#         json.dump(sorted_data, file, indent=4, ensure_ascii=False)


# # Path to the JSON file
# json_file_path = "data_process/scripts_openstreet/selected_tag.json"

# # Sort and save the JSON file
# sort_and_save_json(json_file_path)

# print("JSON file has been sorted and saved.")

# ##################################################################################################
# import json
# import os


# def find_missing_files(json_file, data_folder):
#     # Load JSON data
#     with open(json_file, 'r', encoding='utf-8') as file:
#         data = json.load(file)

#     missing_files = {}

#     for folder, expected_files in data.items():
#         folder_path = os.path.join(data_folder, folder)

#         # Check if folder exists
#         if not os.path.exists(folder_path):
#             missing_files[folder] = expected_files  # All files are missing
#             continue

#         # Get actual files in the folder (without extensions)
#         actual_files = {os.path.splitext(f)[0] for f in os.listdir(
#             folder_path) if f.endswith('.json')}

#         # Find missing files
#         missing = [file for file in expected_files if file not in actual_files]

#         if missing:
#             missing_files[folder] = missing

#     return missing_files


# # File paths
# json_file_path = "data_process/scripts_openstreet/selected_tag.json"
# data_folder_path = "data_process/data_store/new_data"

# # Find missing files
# missing = find_missing_files(json_file_path, data_folder_path)

# # Print or save the results
# if missing:
#     print("Missing files per folder:")
#     for folder, files in missing.items():
#         print(f"{folder}: {files}")
# else:
#     print("All expected files are present.")
# ################################################################################################


import json
import os


def create_filtered_json(json_file, data_folder, output_json):
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    filtered_data = {}

    for folder, expected_files in data.items():
        folder_path = os.path.join(data_folder, folder)

        # If the folder doesn't exist, keep all expected files
        if not os.path.exists(folder_path):
            filtered_data[folder] = expected_files
            continue

        # Get actual files in the folder (without .json extension)
        actual_files = {os.path.splitext(f)[0] for f in os.listdir(
            folder_path) if f.endswith('.json')}

        # Filter out files that already exist
        missing_files = [
            file for file in expected_files if file not in actual_files]

        if missing_files:
            filtered_data[folder] = missing_files

    # Save the filtered data back to a new JSON file
    with open(output_json, 'w', encoding='utf-8') as file:
        json.dump(filtered_data, file, indent=4, ensure_ascii=False)

    print(f"Filtered JSON saved as {output_json}")


# File paths
json_file_path = "data_process/scripts_openstreet/selected_tag.json"
data_folder_path = "data_process/data_store/new_data"
output_json_path = "data_process/scripts_openstreet/missing_files.json"

# Generate the filtered JSON
create_filtered_json(json_file_path, data_folder_path, output_json_path)
