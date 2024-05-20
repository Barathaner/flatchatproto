import os

def apply_function_to_files(root_directory, func):
    """
    Durchläuft alle Dateien in einem Verzeichnisbaum und wendet eine Funktion auf jede Datei an.

    :param root_directory: Der Pfad zum Stammverzeichnis.
    :param func: Die Funktion, die auf jede Datei angewendet werden soll.
    """
    for subdir, dirs, files in os.walk(root_directory):
        for file in files:
            file_path = os.path.join(subdir, file)
            func(file_path)

def apply_function_to_folders(root_directory, func):
    """
    Walks through all subdirectories in a directory tree and applies a function to each folder.

    :param root_directory: The path to the root directory.
    :param func: The function to apply to each folder.
    """
    for subdir, dirs, _ in os.walk(root_directory):
        for dir in dirs:
            folder_path = os.path.join(subdir, dir)
            func(folder_path)