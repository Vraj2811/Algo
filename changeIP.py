import os

def replace_word_in_file(file_path, old_word, new_word):
    with open(file_path, 'r') as file:
        content = file.read()

    content = content.replace(old_word, new_word)

    with open(file_path, 'w') as file:
        file.write(content)

def replace_word_in_directory(directory_path, old_word, new_word, file_extensions):
    for filename in os.listdir(directory_path):
        if filename.endswith(file_extensions):
            file_path = os.path.join(directory_path, filename)
            replace_word_in_file(file_path, old_word, new_word)

directory_path = 'Vraj/htmls'
old_word = '3.110.142.32'
new_word = '3.110.182.250'
file_extensions = (".js", ".html")

replace_word_in_directory(directory_path, old_word, new_word, file_extensions)
