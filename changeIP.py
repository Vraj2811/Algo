import os
import re

def find_first_ip_address(content):
    # Improved regex pattern for valid IPv4 addresses
    ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    match = ip_pattern.search(content)
    if match:
        return match.group()
    else:
        return None

def replace_word_in_file(file_path, new_word):
    try:
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
            print(f"Replacement in {file_path} successful.")
        else:
            print(f"No IP address found in {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")

def replace_word_in_directory(directory_path, new_word, file_extensions):
    if not new_word:
        print("Please enter a non-empty new word.")
        return

    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith(file_extensions):
                file_path = os.path.join(root, filename)
                replace_word_in_file(file_path, new_word)

directory_path = './Algo'
new_word = input("Enter the new word: ")
file_extensions = (".js", ".html")

replace_word_in_directory(directory_path, new_word, file_extensions)
