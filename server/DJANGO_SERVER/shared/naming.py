import re


def natural_key(text):
    return [int(part) if i % 2 else part.lower() for i, part in enumerate(re.split(r'(\d+)', text))]
