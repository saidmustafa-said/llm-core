import re
import json
import time
from src.logger_setup import logger_instance


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        logger = logger_instance.get_logger()
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.debug(
            f"{func.__name__} execution time: {end_time - start_time:.4f} seconds")
        return result
    return wrapper


def extract_json_from_response(response):
    print(response)
    """
    Extract JSON content from the response using multiple methods:
      - Direct parsing of content.
      - Removing function wrappers.
      - Converting Python booleans to JSON booleans.
      - Fallback regex extraction.
    """
    # Extract the content string from the response
    try:
        if isinstance(response, dict):
            content = response.get('choices', [{}])[0].get(
                'message', {}).get('content', '')
        else:
            content = response.json()['choices'][0]['message']['content']
    except Exception as e:
        return {'error': f'Failed to extract content from response: {e}'}

    # Log extracted content if needed
    # print("Extracted content:", content)

    # Cleanup: remove function wrapper tags and any non-JSON prefix/suffix
    cleanup_patterns = [
        r'<function=[^>]*>',  # Remove function prefix
        r'</function>',       # Remove function suffix
        r'^[^{\[]*',          # Remove non-JSON prefix characters
        r'[^}\]]*$',          # Remove non-JSON suffix characters
        r'[\x00-\x1F\x7F]'     # Remove control characters
    ]
    for pattern in cleanup_patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    content = content.strip()

    # Replace Python boolean literals with JSON booleans using regex with word boundaries
    content = re.sub(r'\bTrue\b', 'true', content)
    content = re.sub(r'\bFalse\b', 'false', content)

    # Try direct JSON parsing after cleanup
    try:
        result = json.loads(content)
        return result
    except json.JSONDecodeError as e:
        # If direct parsing fails, try advanced extraction methods.
        extraction_attempts = [
            r'(\{(?:[^{}]|(?R))*\})',  # attempt to capture nested objects
            r'(\[(?:[^\[\]]|(?R))*\])'  # attempt to capture arrays
        ]
        for pattern in extraction_attempts:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                json_str = match.group(0).strip()
                try:
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError:
                    continue

    return {'error': 'Failed to extract valid JSON from response'}
