import os
import sys
import shutil

source_path = "function_pair_with_identical_functionality"
target_project = sys.argv[1]

projects = os.listdir(source_path)
for project in projects:
    if project == target_project :
        pairs = os.listdir(os.path.join(source_path, project))
        for pair in pairs:
            function_files = os.listdir(os.path.join(source_path, project, pair))
            for function_file in function_files:
                with open(os.path.join(source_path, project, pair, function_file), 'r') as input_file:
                    context = input_file.read()
                if context.startswith("None"):
                    os.remove(os.path.join(source_path, project, pair, function_file))