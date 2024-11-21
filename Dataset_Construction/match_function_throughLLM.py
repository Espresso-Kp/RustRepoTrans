import os
import logging
import time
import sys
from generation import generation

source_dir = sys.argv[1]
target_dir = sys.argv[2]
project = sys.argv[3]

# 设置日志配置
logging.basicConfig(filename=f"match_function_throughLLM_{project}.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def process(projects_path, project, target_dir):


    lang_pairs = os.listdir(projects_path)
    for lang_pair in lang_pairs:
        # print(lang_pair)
        if not os.path.exists(os.path.join(target_dir, project, lang_pair)):
            os.makedirs(os.path.join(target_dir, project, lang_pair))
        query_lang = lang_pair.split("__")[0]
        corpus_lang = lang_pair.split("__")[1]

        questions_path = os.listdir(os.path.join(projects_path, lang_pair))
        for question_path in questions_path:

            if os.path.exists(os.path.join(target_dir, project, lang_pair, question_path)):
                logging.info(f"{lang_pair}'s {question_path} already exist")
                continue

            # match
            with open(os.path.join(projects_path, lang_pair, question_path), 'r', encoding='utf-8') as input_file:
                question = input_file.read()
                query_func = question[len("<Target function>\n"):question.find("</Target function>")]

            while True:
                
                try:
                    # match function
                    message = f"You are a professional who is expert in programming language {query_lang} and programming language {corpus_lang}. You will be provided with 1 Target function written in {query_lang} and 10 Possible matching functions written in {corpus_lang}(delimited with XML tags).Please select a function that has the same functionality as the Target function from 10 Possible matching functions.You should only response the serial number of the matching function or \"None\" if it doesn't exit.\n{question}"
                    
                    response = generation(message)

                    # print(f"successfully get {question_path}")
                    with open(os.path.join(target_dir, project, lang_pair, question_path), 'w', encoding='utf-8', errors='ignore') as output_file:
                        # match
                        if response == "None":
                            output_file.write("None")
                            
                        else:
                            start = question.find(f"<Function {response}>") + len(f"<Function {response}>\n")
                            end = question.find(f"</Function {response}>")
                            output_file.write(query_func)
                            output_file.write("------\n")
                            output_file.write(question[start:end])
                    break

                except Exception as e:
                    logging.error(f"error with {lang_pair} {question_path}, detail is: {e}")
                    print(f"error with {lang_pair} {question_path}, detail is: {e}")
                    time.sleep(10)
                    break



if __name__ == "__main__":
    projects_path = os.path.join(source_dir, project) # 替换为实际的文件路径
    process(projects_path, project, target_dir)
