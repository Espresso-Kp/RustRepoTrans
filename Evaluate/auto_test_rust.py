import subprocess
import sys
import os
import re
import shutil
from tree_sitter import Language, Parser
import tree_sitter_rust as tsrust
import logging


translate_result_path = sys.argv[1]
test_result_path = sys.argv[2]
llm = sys.argv[3]
function_pairs_path = sys.argv[4]
dependencies_path = sys.argv[5]


logging.basicConfig(filename=f"auto_test_rust.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RS_LANGUAGE = Language(tsrust.language(), "rust")
parser = Parser()
parser.set_language(RS_LANGUAGE)
query_function_defin_text = """
(
    (function_item) @function.defin
)
"""

query_import_text = """
(
    (use_declaration) @use.name
)
"""
query_function_defin = RS_LANGUAGE.query(query_function_defin_text)
query_import = RS_LANGUAGE.query(query_import_text)



# 运行测试并统计结果
def run_tests(target_project, test_cmd, timeout=700):
    

    result = subprocess.run(test_cmd, cwd=target_project, timeout=timeout, capture_output=True, text=True)
    
    output = result.stdout
    error = result.stderr

    if "deltachat-core" in target_project:
        key = "Summary" in error.split("\n")[-2]
    else:
        key = len(output.split("\n")) >= 3 and output.split("\n")[-3].startswith("test result: ok")
    
    if key:
        return output, error, True
    else:
        return output, error, False

# 解析测试输出并计算通过的测试用例的比例
def parse_test_results(output):
    lines = output.split('\n')
    total_tests = 0
    passed_tests = 0
    for line in lines:
        if 'running ' in line:
            total_tests += int(line.split(' ')[1])
        elif 'test result:' in line:
            passed_tests += int(line.split(' ')[3])
    
    if total_tests > 0:
        pass_ratio = passed_tests / total_tests
    else:
        pass_ratio = 0
    return total_tests, passed_tests, pass_ratio


def extract_translated_function(translated_code):
    node = parser.parse(translated_code).root_node
    function_defin_captures = query_function_defin.captures(node)
    functions_code = []
    for function_defin_capture in function_defin_captures:
        function_defin_node , _ = function_defin_capture
        function_code = translated_code[function_defin_node.start_byte:function_defin_node.end_byte].decode()
        functions_code.append(function_code)
    return functions_code
    
def extract_translated_import(translated_code):
    node = parser.parse(translated_code).root_node

    # get import
    import_codes = []
    import_captures = query_import.captures(node)
    for import_capture in import_captures:
        import_node, _ = import_capture
        import_code = translated_code[import_node.start_byte:import_node.end_byte].decode().strip()
        import_codes.append(f"{import_code}")
    # print(import_codes)
    return import_codes

def read_translated_function(content):
    
    if content == "Too long":
        raise Exception
    
    source_code = None

    pattern = r'<translated function>(.*?)</translated function>'
    translated_result = re.findall(pattern, content, re.DOTALL)[0].strip()

    translated_function = None

    patterns = [r'```rust(.*?)```',r'```Rust(.*?)```', r'<rust function>(.*?)</rust function>', r'<rust function translation>(.*?)</rust function translation>', r'<rust translated function>(.*?)</rust translated function>']

    for pattern in patterns:
        if not translated_function:
            try:
                translated_code = re.findall(pattern, translated_result, re.DOTALL)[0].strip()
                translated_code = bytes(translated_code, "utf-8")
                
                translated_function = extract_translated_function(translated_code)
                translated_code_import = extract_translated_import(translated_code)
            except:
                translated_function = None
        else:
            break
    
    if not translated_function:
        translated_code = translated_result
        translated_code = bytes(translated_code, "utf-8")
        translated_function = extract_translated_function(translated_code)
        translated_code_import = extract_translated_import(translated_code)
    

    return source_code, translated_function, translated_code_import

def change_target_function(function_path, source_code, translated_function, translated_code_import):
    with open(function_path, 'r', encoding='utf-8', errors='ignore') as input_file:
        content = input_file.read()

    # 替换function
    content = content.replace(source_code,  "\n" + translated_function+ "\n")
    
    # 剔除重复导入的库
    final_code_import = "\n"
    # print(translated_code_import)
    for import_code in translated_code_import:
        if import_code not in content:
            final_code_import += import_code + "\n"
    # print(final_code_import)
    content = content.split("\n")
    # 找到 "use" 第一次出现的位置
    index = next((i for i, x in enumerate(content) if x.startswith("use ") and x.endswith(";")), None)
    # print(index)
    if final_code_import != "\n":
        if index != -1:
            content.insert(index, final_code_import)
        else:
            content.insert(0, final_code_import)
    # content = translated_code_import + "\n" + content
    content = "\n".join(content)

    with open(function_path, 'w', encoding='utf-8', errors='ignore') as output_file:
        output_file.write(content)

def run(target_llm, target_project, target_lang, test_cmd):

    translated_function_files = os.listdir(os.path.join(translate_result_path, target_llm, target_project, target_lang))
    # print(len(translated_function_files))
    

    if not os.path.exists(os.path.join(test_result_path, target_llm, target_project, target_lang)):
        os.makedirs(os.path.join(test_result_path, target_llm, target_project, target_lang))

    for translated_function_file in translated_function_files:
        if os.path.exists(os.path.join(test_result_path, target_llm, target_project, target_lang, translated_function_file)):
            logging.info(f"already get {target_llm}:{translated_function_file}")
            continue

        # 读取翻译结果
        function_path = "/".join(translated_function_file.split("__.rs")[0].split("__")) + ".rs" 

        # deltachat-core 专有
        if target_project == "deltachat-core":
            function_path = function_path.replace("rust/", "rust/src/")
        # print(translated_function_file)
        
        # 保存原文件
        shutil.copyfile(function_path, function_path + ".copy")
        

        try :
            with open(os.path.join(translate_result_path, target_llm, target_project, target_lang, translated_function_file), 'r', encoding='utf-8', errors='ignore') as input_file:
                content = input_file.read()
            source_code, translated_function, translated_code_import = read_translated_function(content)
            with open(os.path.join(function_pairs_path, target_project, target_lang, translated_function_file),  'r', encoding='utf-8', errors='ignore') as input_file:
                content = input_file.read().split("------")[0]
                pattern = r'<function>(.*?)</function>'
                source_code = re.findall(pattern, content, re.DOTALL)[0].strip()
            # 剔除重复定义的函数
            with open(os.path.join(dependencies_path, target_project, target_lang, "rust", translated_function_file), "r") as input_file:
                content = input_file.read()
            
            final_translated_function = "\n"
            for function in translated_function:
                if function not in content:
                    final_translated_function += function + "\n"
            translated_function = final_translated_function

            # 更换目标函数
            change_target_function(function_path, source_code, translated_function, translated_code_import)

            output, error, result = run_tests(os.path.join("projects", target_project, "rust"), test_cmd)

            test_result = "Success" if result else "Fail"
            print(f"{test_result}: {target_lang} {translated_function_file} {function_path}")

            # 记录测试结果
            with open(os.path.join(test_result_path, target_llm, target_project, target_lang, translated_function_file), 'w') as output_file:
                output_file.write(test_result)
                # if not result:
                output_file.write(f"\nfile path is :\n{function_path}\n\n")
                output_file.write(f"output is:\n{output}\n\n")
                output_file.write(f"error is :\n{error}\n")
            
        except KeyboardInterrupt :
            break
        except Exception as e:
            print(f"there is error: {translated_function_file}, the error is {e}")
            with open(os.path.join(test_result_path, target_llm, target_project, target_lang, translated_function_file), 'w') as output_file:
                output_file.write(f"error\nthe error is {e}")
        finally:
            # 还原文件
            shutil.copyfile(function_path + ".copy", function_path)
            # 删除备份
            os.remove(function_path + ".copy")
            # break
            # pass

        
def main():
    special_test_cmds = {"deltachat-core": ["cargo","nextest","run"], "incubator-milagro-crypto" : ["cargo", "test", "--all", "--all-features", "--release"], "iceberg" : ["make", "unit-test"]}

    target_llms = os.listdir(translate_result_path)

    for target_llm in target_llms:
        if llm not in target_llm:
            continue
        target_projects = os.listdir(os.path.join(translate_result_path, target_llm))
        for target_project in target_projects:
            test_cmd = ["cargo", "test"] if target_project not in special_test_cmds.keys() else special_test_cmds[target_project]
            lang_pairs = os.listdir(os.path.join(translate_result_path, target_llm, target_project))
            for lang_pair in lang_pairs:
                run(target_llm, target_project, lang_pair, test_cmd)
        
# 构建环境变量
env = os.environ.copy()
env["PATH"] = os.environ["PATH"]

if __name__ == "__main__":
    main()
