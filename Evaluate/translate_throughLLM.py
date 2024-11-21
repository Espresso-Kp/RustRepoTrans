import os
import logging
import time
import sys
import re

from generation import generation

source_dir = sys.argv[1]
target_dir = sys.argv[2]
llm = sys.argv[3]
dependencies_path = sys.argv[4]

# 设置日志配置
logging.basicConfig(filename=f"translate_throughLLM_{llm}.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
                logging.info(f"{lang_pair}'s {question_path} already exists")
                continue
            else:
                print(os.path.join(target_dir, project, lang_pair, question_path))

            # translte
            with open(os.path.join(projects_path, lang_pair, question_path), 'r', encoding='utf-8',  errors='ignore') as input_file:
                question = input_file.read().split("------")

                pattern = r'<function>(.*?)</function>'
                query_func = re.findall(pattern, question[0], re.DOTALL)[0].strip()

                corpus_func = re.findall(pattern, question[1], re.DOTALL)[0].strip()
                
                query_func_signature = query_func.split("{")[0]

            # with use package
            try:
                with open(os.path.join(dependencies_path, project, lang_pair, "rust", question_path), 'r', encoding='utf-8',  errors='ignore') as input_file:
                    content = input_file.read()

                content = content.split("------")
                related_function_and_datatype = content[0]
                use_package = content[1]
            except:
                logging.info(f"{lang_pair}'s {question_path} without dependencies file")
                continue
            
            while True:
                try:
                    message = f"Translate the given {corpus_lang} function to {query_lang} according to the {query_lang} function signature, {query_lang} function dependencies(including function and variable dependencies), and data type declarations and {query_lang} function dependency libraries I provide(delimited with XML tags).Make sure to call the relevant dependencies as much as possible in the translated function Only response the translated function results.\n<{corpus_lang} function>\n{corpus_func}\n</{corpus_lang} function>\n<{query_lang} function signature>\n{query_func_signature}\n</{query_lang} function signature>\n<{query_lang} function dependencies, and data type declarations>\n{related_function_and_datatype}\n</{query_lang} function dependencies and data type declarations>\n<{query_lang} function dependency libraries>{use_package}\n</{query_lang} function dependency libraries>\n"

                    response = generation(message)

                    print(f"successfully get {question_path}")
                    with open(os.path.join(target_dir, project, lang_pair, question_path), 'w', encoding='utf-8', errors='ignore') as output_file:
                        # translate
                        output_file.write(f"<message>\n{message}\n</message>\n")
                        output_file.write(f"<function>\n{query_func}\n</function>\n<translated function>\n{response}</translated function>")
                        output_file.write(response)
                    break
                
                except Exception as e:
                    logging.error(f"error with {lang_pair} {question_path}, detail is: {e}")
                    print(f"error with {lang_pair} {question_path}, detail is: {e}")
                    time.sleep(10)
                    break



if __name__ == "__main__":

    projects = os.listdir(source_dir)
    for project in projects:
        process(os.path.join(source_dir, project), project, os.path.join(target_dir, f"translate_by_{llm}"))
