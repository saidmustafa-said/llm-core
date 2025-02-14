"""
Script to Convert Raw Data to an Advanced Fine-Tuning Format

Raw data in "data.json" is assumed to be in the format:
[
    {
        "name": "İstanbul Surları",
        "description": "No description available",
        "location": "Türkiye/İstanbul",
        "coordinates": {
            "latitude": 41.0142069,
            "longitude": 28.9312722
        },
        "tags": [
            "attraction"
        ]
    },
    {
        "name": "Ayasofya-i Kebir Câmi-i Şerifi",
        "description": "No description available",
        "location": "Türkiye/İstanbul",
        "coordinates": {
            "latitude": 41.0084634,
            "longitude": 28.9798633
        },
        "tags": [
            "museum"
        ]
    },
    ...
]

This script converts each record into the format required for fine‑tuning:
    - "input_text": A synthetic query prompt generated using the record's location, name (if available), description (if available), and tags.
    - "target_text": A JSON-formatted string of the original record.

The generated prompt is designed so that if the provided details are too broad, the model is instructed to recommend 3–4 options based on the tags. For example, the prompt might be:

    "I am located in Türkiye/İstanbul. I would like to learn more about a place called 'Ayasofya-i Kebir Câmi-i Şerifi'. If my query is broad, please recommend 3-4 options associated with the tags: museum."

If the name is missing or is "unknown" and/or the description is "No description available", those details are omitted from the prompt.

Finally, the processed data is split into training (80%), validation (10%), and test (10%) sets and saved as "train_data.json", "eval_data.json", and "test_data.json" respectively.
"""

import json
import random


def create_input_text(record):
    """
    Create an advanced synthetic user query based on the raw record.

    - Uses the 'location' field.
    - If the 'name' field is present and not "unknown", includes a sentence about the name.
    - If the 'description' field is present and not "No description available", includes the description.
    - Always includes an instruction to recommend 3–4 options if the query is broad, using the available tags.
    """
    location = record.get("location", "").strip() or "an unknown location"

    name = record.get("name", "").strip()
    name_sentence = f"I would like to learn more about a place called '{name}'. " if name and name.lower(
    ) != "unknown" else ""

    description = record.get("description", "").strip()
    description_sentence = f"The description provided is: '{description}'. " if description and description.lower(
    ) != "no description available" else ""

    tags = record.get("tags", [])
    tags_text = ", ".join(tags) if tags else "no tags"

    recommendation_sentence = f"If my query is broad, please recommend 3-4 options associated with the tags: {tags_text}."

    prompt = f"I am located in {location}. {name_sentence}{description_sentence}{recommendation_sentence}"
    return prompt


def process_raw_data(raw_data):
    """
    Convert raw records into the fine-tuning format.

    Each output record is a dictionary with:
        - "input_text": The synthetic query prompt.
        - "target_text": The JSON string representing the original record.
    """
    processed = []
    for record in raw_data:
        input_text = create_input_text(record)
        target_text = json.dumps(record, ensure_ascii=False)
        processed.append({
            "input_text": input_text,
            "target_text": target_text
        })
    return processed


def split_data(data, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
    """
    Split the data into train, validation, and test sets.
    The provided ratios should sum to 1.0.
    """
    if not abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6:
        raise ValueError("Train, validation, and test ratios must sum to 1.0.")

    total_samples = len(data)
    random.shuffle(data)

    train_end = int(train_ratio * total_samples)
    val_end = train_end + int(val_ratio * total_samples)

    return data[:train_end], data[train_end:val_end], data[val_end:]


def main():
    raw_data_path = "new_data/nodes/amenity.json"

    with open(raw_data_path, "r", encoding="utf-8") as infile:
        raw_data = json.load(infile)

    processed_data = process_raw_data(raw_data)
    print(f"Processed {len(processed_data)} records.")

    train_data, val_data, test_data = split_data(
        processed_data, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1)

    print(f"Train samples: {len(train_data)}")
    print(f"Validation samples: {len(val_data)}")
    print(f"Test samples: {len(test_data)}")

    output_files = {
        "train_data.json": train_data,
        "eval_data.json": val_data,
        "test_data.json": test_data,
    }

    for filename, dataset in output_files.items():
        with open(f"data2/{filename}", "w", encoding="utf-8") as outfile:
            json.dump(dataset, outfile, ensure_ascii=False, indent=4)
        print(f"Saved {len(dataset)} records to {filename}")


if __name__ == "__main__":
    random.seed(42)
    main()
