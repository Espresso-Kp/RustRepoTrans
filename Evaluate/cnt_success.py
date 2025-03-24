import os
import sys


def count_success_files(test_result, target_llm, target_project, lang_pair):
    directory = os.path.join(test_result, target_llm, target_project, lang_pair)
    success_count = 0
    total_count = 0
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        if os.path.isfile(file_path):
            total_count += 1

            with open(file_path, 'r') as file:
                content = file.read().strip()
                if content.startswith("Success"):
                    success_count += 1



    return total_count, success_count

test_result = sys.argv[1]
target_llm = sys.argv[2]
llms = os.listdir(test_result)
for llm in llms:
    if target_llm not in llm:
        continue
    target_projects = os.listdir(os.path.join(test_result, llm))
    llm_success_count = 0
    llm_total_count = 0
    for target_project in target_projects:
        lang_pairs = os.listdir(os.path.join(test_result, llm, target_project))
        for lang_pair in lang_pairs:
            total_count, success_count = count_success_files(test_result, llm, target_project, lang_pair)
            llm_success_count += success_count
            llm_total_count += total_count

    print(f"{target_llm}'s pass@1 on RustRepoTrans is {float(llm_success_count) / llm_total_count}")
