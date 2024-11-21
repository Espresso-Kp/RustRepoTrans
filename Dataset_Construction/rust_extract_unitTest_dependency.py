from tree_sitter import Language, Parser
import tree_sitter_rust as tsrust
import sys
import os
import re
import shutil

RS_LANGUAGE = Language(tsrust.language(), "rust")
parser = Parser()
parser.set_language(RS_LANGUAGE)
# call_functions = []

# 获取impl定义
query_impl_defin_text = """
(
    (impl_item) @impl.defin
)
"""


# 获取[test]定义


query_test_defin_text = """
(
    (attribute_item) @test.defin
)
"""

# 获取函数定义
query_function_defin_text = """
(
    (function_item) @function.defin
)
"""

query_function_name_text = """
(function_item
  (identifier) @function.name)
"""

# 获取macro定义
query_macro_defin_text = """
(
    (macro_definition) @macro.defin
)
"""

query_macro_name_text = """
(macro_definition
  (identifier) @macro.name)
"""

# 获取struct定义
query_struct_defin_text = """
(
    (struct_item) @struct.defin
)
"""
query_struct_name_text = """
(struct_item
    (type_identifier) @struct.name
)
"""

# 调用的函数
query_call_function_text = """
(
    (call_expression) @function.call
)
"""
query_call_function_name_text = """
(
  (field_identifier) @function.call_name
)
"""



# 调用的macro
query_call_macro_text = """
(
    (macro_invocation) @macro.call
)
"""
query_call_macro_name_text = """
(macro_invocation
  (identifier) @macro.call_name)
"""

# test case中如果出于macro调用里的函数会从call_expression变成identifier
query_call_macro_call_function_text = """
(
    (identifier) @macro.call_function
)
"""

# 调用的数据类型
query_call_vars_type_text = """
(
    (type_identifier) @call_vars.type
)
"""

# 调用的变量
query_call_vars_text = """
(
    (expression_statement) @call_vars.exp
)
(
    (let_declaration) @call_vars.let
)
"""

query_call_vars_name_text = """
(
    (field_identifier) @call_vars.let
)
"""

query_import_text = """
(
    (use_declaration) @use.name
)
"""

# Create a query object
query_test_defin = RS_LANGUAGE.query(query_test_defin_text)
query_impl_defin = RS_LANGUAGE.query(query_impl_defin_text)
query_function_defin = RS_LANGUAGE.query(query_function_defin_text)
query_function_name = RS_LANGUAGE.query(query_function_name_text)
query_macro_defin = RS_LANGUAGE.query(query_macro_defin_text)
query_macro_name = RS_LANGUAGE.query(query_macro_name_text)
query_struct_defin = RS_LANGUAGE.query(query_struct_defin_text)
query_struct_name = RS_LANGUAGE.query(query_struct_name_text)
query_call_function = RS_LANGUAGE.query(query_call_function_text)
query_call_function_name = RS_LANGUAGE.query(query_call_function_name_text)
query_call_macro = RS_LANGUAGE.query(query_call_macro_text)
query_call_macro_name = RS_LANGUAGE.query(query_call_macro_name_text)
query_call_macro_call_function = RS_LANGUAGE.query(query_call_macro_call_function_text)
query_call_vars = RS_LANGUAGE.query(query_call_vars_text)
query_call_vars_name = RS_LANGUAGE.query(query_call_vars_name_text)
query_call_vars_type = RS_LANGUAGE.query(query_call_vars_type_text)
query_import = RS_LANGUAGE.query(query_import_text)



def traverse_call(node, source_code, call_functions):
    if node.type == "call":
        call_functions.append(node)
        function_call_code = source_code[node.start_byte:node.end_byte].decode('utf-8')
        # print(f"Function call (traversal): {function_call_code}")
    for child in node.children:
        traverse_call(child, source_code, call_functions)


def traverse(node, source_code, depth=0):
    # Get the node text
    node_text = source_code[node.start_byte:node.end_byte].decode('utf-8')
    for child in node.children:
        traverse(child, source_code, depth + 1)

# Execute the query to get the captures


def get_source_code(target_file_path):

    with open(target_file_path, 'r', encoding='utf-8', errors='ignore') as input_file:
        source_code = input_file.read()

    # 转化成bytes！！否则在出现中文注释时，根据偏移获得对应内容会出错
    source_code = bytes(source_code, "utf-8")

    return source_code

def get_source_code_and_path(target_file_path):
    with open(target_file_path, 'r', encoding='utf-8', errors='ignore') as input_file:
        content = input_file.read()
        
        content = content.split("------")[0]

        pattern = r'<path>(.*?)</path>'
        function_path = re.findall(pattern, content, re.DOTALL)[0].strip()

        pattern = r'<function>(.*?)</function>'
        source_code = re.findall(pattern, content, re.DOTALL)[0].strip()

    # 转化成bytes！！否则在出现中文注释时，根据偏移获得对应内容会出错
    source_code = bytes(source_code, "utf-8")

    return source_code, function_path

def get_call_macro(node, source_code):
    call_macro_names = set()
    # 获取依赖数据类型
    call_macro_captures = query_call_macro.captures(node)
    for call_macro_capture in call_macro_captures:
        call_macro_node , _ = call_macro_capture

        # 获取call macro
        call_macro_name_capture = query_call_macro_name.captures(call_macro_node)
        try:
            call_macro_name_node , _ = call_macro_name_capture[0]
            call_macro_code = source_code[call_macro_name_node.start_byte:call_macro_name_node.end_byte].decode()
            call_macro_names.add(call_macro_code)
        except:
            pass

        # 获取call macro中调用的函数
        call_macro_call_function_capture = query_call_macro_call_function.captures(call_macro_node)
        for call_macro_call_function_node, _ in call_macro_call_function_capture:
            call_macro_call_function_code = source_code[call_macro_call_function_node.start_byte:call_macro_call_function_node.end_byte].decode()
            call_macro_names.add(call_macro_call_function_code)

    return call_macro_names

def get_call_function(node, source_code):
    call_function_names = set()
    call_function_captures = query_call_function.captures(node)

    

    for call_function_capture in call_function_captures:
        call_function_node, _ = call_function_capture

        # call function
        call_function_var_code = source_code[call_function_node.start_byte:call_function_node.end_byte].decode()
        call_function_var_code = call_function_var_code.split("=")
        for call_function_var in call_function_var_code:
            if "(" in call_function_var and ")" in call_function_var:
                call_function_var = call_function_var.replace("\n", "")
                call_function_var = call_function_var.split("self.")[-1]
                pattern = r'([a-zA-Z_][a-zA-Z0-9_:]*)\.|([a-zA-Z_][a-zA-Z0-9_:]*\([^\)]*\))'
                call_function_var = re.findall(pattern, call_function_var)
                call_function = [match[1].split("(")[0] for match in call_function_var if match[1]]

                call_function_names.update(call_function)
            
    return call_function_names

def get_call_vars_type(node, source_code):
    call_vars_type_name = set()
    # 获取依赖数据类型
    vars_type_captures = query_call_vars_type.captures(node)
    for vars_type_capture in vars_type_captures:
        vars_type_node , _ = vars_type_capture
        vars_type_code = source_code[vars_type_node.start_byte:vars_type_node.end_byte].decode()
        call_vars_type_name.add(vars_type_code)
    return call_vars_type_name

def get_file_function_dependency(target_file_path):
    
    Dependency_func = {}
    Dependency_vars = {}

    source_code = get_source_code(target_file_path)
    function_path = target_file_path
    tree = parser.parse(source_code)


    test_function_captures = query_test_defin.captures(tree.root_node)
    for capture in test_function_captures:
        node, _ = capture

        attribute_name = source_code[node.start_byte:node.end_byte].decode()
        if "test" not in attribute_name:
            continue

        function_node = node.next_sibling 
        function_name_captures = query_function_name.captures(function_node)
        for capture in function_name_captures:
            function_name_node, _ = capture
            function_name = source_code[function_name_node.start_byte:function_name_node.end_byte].decode()
            # 先获取全部函数再减去impl函数
            if function_name in Dependency_func.keys():
                continue
            
            # 从测试文件中提取覆盖的函数
            # if not function_name.startswith("test"):
                # print(function_name)
                # continue

            call_function_names = get_call_function(function_node, source_code)
            call_macro_names = get_call_macro(function_node, source_code)

            call_function_names.update(call_macro_names)
            Dependency_func[function_name] = call_function_names


    return Dependency_func, Dependency_vars, function_path


def filtered_os_walk(top):
    for root, dirs, files in os.walk(top):
        # 过滤掉名字以"."开头的目录和名字包含"test"的目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and 'test' not in d]
        yield root, dirs, files

def get_function_defin(node, source_code, function_name_to_code, project_functions, file_path):
    function_defin_captures = query_function_defin.captures(node)
    function_names = set()
    for function_defin_capture in function_defin_captures:
        function_defin_node , _ = function_defin_capture
        function_code = source_code[function_defin_node.start_byte:function_defin_node.end_byte].decode()
        function_name_captures = query_function_name.captures(function_defin_node)
        function_name_node, _ = function_name_captures[0]
        function_name = source_code[function_name_node.start_byte:function_name_node.end_byte].decode()

        function_names.add(function_name)
        # 以@为分隔符，将函数的文件路径加入，防止在单个项目中存在多个同名函数
        function_name_to_code[file_path + "@" + function_name] = function_code
    project_functions[file_path] = function_names

def get_struct_defin(node, source_code, struct_name_to_code, project_structs, file_path):
    struct_names = set()
    struct_defin_captures = query_struct_defin.captures(node)
    for struct_defin_capture in struct_defin_captures:
        struct_defin_node , _ = struct_defin_capture
        struct_defin_code = source_code[struct_defin_node.start_byte:struct_defin_node.end_byte].decode()
        struct_name_captures = query_struct_name.captures(struct_defin_node)
        sturct_name_node, _ = struct_name_captures[0]
        sturct_name = source_code[sturct_name_node.start_byte:sturct_name_node.end_byte].decode()
        struct_names.add(sturct_name)
        struct_name_to_code[file_path + "@" + sturct_name] = struct_defin_code

    project_structs[file_path] = struct_names

def get_macro_defin(node, source_code, macro_name_to_code, project_macros, file_path):
    macro_names = set()
    macro_defin_captures = query_macro_defin.captures(node)
    for macro_defin_capture in macro_defin_captures:
        macro_defin_node , _ = macro_defin_capture
        macro_defin_code = source_code[macro_defin_node.start_byte:macro_defin_node.end_byte].decode()
        macro_name_captures = query_macro_name.captures(macro_defin_node)
        macro_name_node, _ = macro_name_captures[0]
        macro_name = source_code[macro_name_node.start_byte:macro_name_node.end_byte].decode()

        macro_names.add(macro_name)

        macro_name_to_code[file_path + "@" + macro_name] = macro_defin_code
    project_macros[file_path] = macro_names

# 读取项目
def get_project_functions(project_path):

    project_functions = {}
    project_structs = {}
    project_macros = {}

    function_name_to_code = {}
    struct_name_to_code = {}
    macro_name_to_code = {}

    project_imports = {}
    project_vars = {}

    # 手动添加
    project_structs["IString"] = ["IString"]
    struct_name_to_code["IString@IString"] = "pub type IString = ::string_cache::Atom<IStringStaticSet>;"

    # for current_path, _, files in filtered_os_walk(project_path):
    for current_path, _, files in os.walk(project_path):
        for file in files:
            # if "test" in file:
            #     continue
            if file.endswith(".rs"):

                file_path = os.path.join(current_path, file)
                source_code = get_source_code(file_path)
                tree = parser.parse(source_code)
                
                # get function defin
                get_function_defin(tree.root_node, source_code, function_name_to_code, project_functions, file_path)
                 
                # get struct defin
                get_struct_defin(tree.root_node, source_code, struct_name_to_code, project_structs, file_path)
                
                # get macro defin
                get_macro_defin(tree.root_node, source_code, macro_name_to_code, project_macros, file_path)

                # get import
                import_codes = []
                import_captures = query_import.captures(tree.root_node)
                for import_capture in import_captures:
                    import_node, _ = import_capture
                    import_code = source_code[import_node.start_byte:import_node.end_byte].decode().split("use")[-1].strip()
                    import_codes.append(import_code)
                project_imports[file_path] = import_codes

    # 将macro归入function
    for file_path, macros in project_macros.items():
        if file_path in project_functions.keys():
            project_functions[file_path].update(macros)  
    function_name_to_code = {**macro_name_to_code, **function_name_to_code}

    return project_imports, project_functions, function_name_to_code, project_structs, struct_name_to_code

def match(project_functions, dependency_funcs, function_path, project_imports):
    # 依次进行匹配
    project_dependency_function = {}

    for target_function , call_functions in dependency_funcs.items():
        dependencies = []
        for call_function in call_functions:
            key = False
            # 先从同个文件中找
            for file_path, potential_functions in project_functions.items():
                if file_path == function_path:
                    if call_function in potential_functions:
                        dependencies.append(function_path + "@" + call_function)
                        key = True
                    break
            if key:
                continue

            # 从import中找
            for project_file_path, file_imports in project_imports.items():
                # 获得目标文件的对应import
                if project_file_path == function_path:
                    for file_path, potential_functions in project_functions.items():
                        # 获取文件名simple_path，判断该文件是否在目标文件的import中
                        # 如果在file_import中，那么目标文件可以使用该文件内的函数
                        simple_path = file_path.split("/")[-1].split(".")[0].strip()
                        
                        for file_import in file_imports:
                            if simple_path in file_import:
                                if call_function in potential_functions:
                                    dependencies.append(file_path + "@" + call_function)
                                    key = True
                                break
                        if key:
                            break
                    break
            if key:
                continue

        project_dependency_function[target_function] = dependencies

    return project_dependency_function





project_name = sys.argv[1]
target_lang = sys.argv[2]

project_path = os.path.join("projects", project_name, target_lang)
target_files_path = project_path
project_imports, project_functions, function_name_to_code, project_structs, struct_name_to_code  = get_project_functions(project_path)



unit_test_function = set()
unitTest_cnt = 0
for current_path, _, target_files in os.walk(target_files_path):
    for target_file in target_files:
        if not target_file.endswith(".rs"):
            continue
        
        
        dependency_funcs, dependency_vars, function_path = get_file_function_dependency(os.path.join(current_path, target_file))
        # Dependency, function_path = get_file_function_dependency(target_file)
        
        if not dependency_funcs:
            continue
        
        unitTest_cnt += len(dependency_funcs)
        result_function = match(project_functions, dependency_funcs, function_path, project_imports)
        

        
        for function, call_functions in result_function.items():
            unit_test_function.update(call_functions)

# 将有测试用例的函数复制到目标文件夹中
cnt = 0
functions = set()
function_with_unit_test = set()
function_files = os.listdir(f"functions/{project_name}/{target_lang}")

if not os.path.exists(f"functions_with_unitTest/{project_name}/{target_lang}"):
    os.makedirs(f"functions_with_unitTest/{project_name}/{target_lang}")

for function_file in function_files:
    with open(os.path.join(f"functions/{project_name}/{target_lang}", function_file), 'r', encoding='utf-8', errors='ignore') as input_file:
        content = input_file.read()
    

    pattern = r'<path>(.*?)</path>'
    function_path = re.findall(pattern, content, re.DOTALL)[0].strip()

    pattern = r'<function>(.*?)</function>'
    source_code = re.findall(pattern, content, re.DOTALL)[0].strip()

    pattern = r'fn (.*?)(\<.*?\>)?\('
    function_name = re.findall(pattern, source_code, re.DOTALL)[0][0].strip()

    function_name = function_path + "@" + function_name

    if function_name in unit_test_function:
        functions.add(function_name)
        cnt += 1
        shutil.copy(os.path.join(f"functions/{project_name}/{target_lang}", function_file), os.path.join(f"functions_with_unitTest/{project_name}/{target_lang}", function_file))
        
