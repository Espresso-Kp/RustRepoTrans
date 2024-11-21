import re
import os
import sys


total_functions = set()

def extract_functions_from_code(code, pattern):
    
    function_head_pattern = re.compile(pattern)

    lines = code.split('\n')
    functions = []
    brace_count = 0
    function_code = []
    inside_function = False
    key = False
    for i, line in enumerate(lines):
        if not inside_function and function_head_pattern.search(line):
            inside_function = True

        if inside_function:
            function_code.append(line)
            if not line.lstrip(" ").startswith("//"):
                brace_count += line.count('{')
                brace_count -= line.count('}')
            if brace_count == 0 :
                if line.strip().endswith('}'):
                    inside_function = False
                    functions.append('\n'.join(function_code))
                    function_code = []
                elif line.strip().endswith(';'):
                    inside_function = False
                    function_code = []
    return functions

def extract_functions_from_code_py(code):
    lines = code.split('\n')
    functions = []
    function_code = []
    inside_function = False
    
    for line in lines:
        if not inside_function and line.lstrip().startswith("def "):
            # 获取函数起始的缩进长度
            pre_cnt = len(line) - len(line.lstrip())
            function_code.append(line)
            inside_function = True
            # 跳过def那一行
            continue
        
        if inside_function:
            # 空行和缩进比def要小表示还在函数内
            if len(line) == 0 or len(line) - len(line.lstrip()) >= pre_cnt + 4:
                function_code.append(line)
            else:
                functions.append('\n'.join(function_code))
                function_code = []
                # 当前行有可能是下一个函数的声明行，不处理会跳过该函数
                if line.lstrip().startswith("def "): 
                    pre_cnt = len(line) - len(line.lstrip())
                    function_code.append(line)
                else:
                    inside_function = False
    
    # 处理在文件末尾声明定义的function
    if function_code:
        functions.append('\n'.join(function_code))
    
    return functions
    
def extract_functions_from_code_rb(code):
    lines = code.split('\n')
    functions = []
    function_code = []
    inside_function = False
    
    for line in lines:
        if not inside_function and line.lstrip().startswith("def "):
            # 获取函数起始的缩进长度
            pre_cnt = len(line) - len(line.lstrip())
            function_code.append(line)
            inside_function = True
            # 跳过def那一行
            continue
        
        if inside_function:
            if len(line) - len(line.lstrip()) == pre_cnt and line.lstrip().startswith("end"):
                inside_function = False
                functions.append('\n'.join(function_code))
                function_code = []
            else:
                function_code.append(line)
    
    return functions

def save_functions_to_files(functions, output_dir, output_file_name):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    try:
        for i, func in enumerate(functions):
            # influxdb-1.8\\client\\influxdb_test.go -> influxdb-1.8__client__influxdb_test
            output_file = os.path.splitext(output_file_name)
            output_file = output_file[0].replace("/", "__") + "__" + output_file[1]
            file_path = os.path.join(output_dir, f'{output_file}__function__{i + 1}.txt')
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(f"<path>\n{output_file_name}\n</path>\n")
                file.write(f"<function>\n{func}\n</function>")
    except Exception as e:
        print(e)
        pass

def process_file(input_file, lang, output_dir, pattern):

    with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
        code = file.read()
    
    if lang == "py":
        functions = extract_functions_from_code_py(code)
    elif lang == "rb":
        functions = extract_functions_from_code_rb(code)
    else:
        functions = extract_functions_from_code(code, pattern)

    save_functions_to_files(functions, output_dir, input_file)

def main():
    project_dir = "projects"
    target_project = sys.argv[1]

    
    patterns = {
        'cpp': r'^\s*[\w\s\*\[\]\<\>\:]+\s+[\w\s\*\[\]\<\>\:]+\s*\(',
        'cxx': r'^\s*[\w\s\*\[\]\<\>\:]+\s+[\w\s\*\[\]\<\>\:]+\s*\(',
        'h': r'^\s*[\w\s\*\[\]\<\>\:]+\s+[\w\s\*\[\]\<\>\:]+\s*\(',
        'java': r'^\s*(public|protected|private|static|final|synchronized|native|abstract|strictfp|default)?\s*(public|protected|private|static|final|synchronized|native|abstract|strictfp|default)?\s*[\w\<\>\[\] ]+\s+[\w\<\>\[\]]+\s*\(',
        'rs': r'^\s*(unsafe)?\s*(pub(\(crate\))?)?\s*(async)?\s*fn\s',
        'c': r'^\s*[\w\s\*\[\]]*\s*\w+\s*\(',
        'py': r''
    }
    lang_to_fileType = {
        'cpp' : ['cpp', 'cxx', 'h'],
        'c' : ['c', 'h'],
        'java' : ['java'],
        'rust' : ['rs'],
        'python' : ['py']
    }
    
    projects = os.listdir(project_dir)
    for project in projects:
        if project != target_project:
            continue
        project_pair_path = os.path.join(project_dir, project)
        langs = os.listdir(project_pair_path)
        for lang in langs:
            root_dir = os.path.join(project_pair_path, lang)
            # 对项目进行遍历
            for current_path, dirs, files in os.walk(root_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    try :
                        file_lang = file.split('.')[-1]
                    except:
                        continue
                    if file_lang in lang_to_fileType[lang]:
                        file_path = os.path.join(current_path, file)
                        if "test" in file_path or "Test" in file_path:
                            continue
                        process_file(file_path, file_lang, root_dir.replace("projects", "functions"), patterns[file_lang])


if __name__ == '__main__':
    main()
