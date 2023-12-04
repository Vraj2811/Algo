import os
import re

def find_first_ip_address(content):
    # Regular expression to find an IP address in the content
    ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    match = ip_pattern.search(content)
    if match:
        return match.group()
    else:
        return None

def replace_word_in_file(file_path, new_word):
    with open(file_path, 'r') as file:
        content = file.read()

    # Find the first IP address in the content
    old_word = find_first_ip_address(content)

    if old_word:
        print(f"Found IP address in {file_path}: {old_word}")
        # Replace the old word with the new word
        content = content.replace(old_word, new_word)

        with open(file_path, 'w') as file:
            file.write(content)
    else:
        print(f"No IP address found in {file_path}")

def replace_word_in_directory(directory_path, new_word, file_extensions):
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith(file_extensions):
                file_path = os.path.join(root, filename)
                replace_word_in_file(file_path, new_word)

# directory_path = 'Vraj/htmls'
directory_path = 'htmls'
new_word = input("Enter the new word: ")
file_extensions = (".js", ".html")

replace_word_in_directory(directory_path, new_word, file_extensions)
