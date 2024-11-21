from rank_bm25 import BM25Plus
import os
import sys
import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer


def read_corpus(corpus_files_path):
    corpus = []

    corpus_files = os.listdir(corpus_files_path)
    for corpus_file in corpus_files:
        with open(os.path.join(corpus_files_path, corpus_file), 'r') as input_file:
            tmp = input_file.read()

            corpus.append(tmp)
    
    return corpus

def normalize_text(text):
    # 大小写归一化
    text = text.lower()
    
    # 分词
    words = re.findall(r'\w+|[^\s\w]+', text)
    
    # 去除停用词
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words]
    
    # 词干提取
    stemmer = PorterStemmer()
    words = [stemmer.stem(word) for word in words]
    
    # 词形还原
    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(word) for word in words]
    
    return words


# 使用正则表达式进行分词
def tokenize_code(code):
    # 使用归一化
    return normalize_text(code)

def main():
    corpus_files_path = "functions"
    query_files_path = "functions_with_unitTest"
    match_results_path = "potential_function_pair"

    project = sys.argv[1]
    corpus_lang = sys.argv[2]
    query_lang = sys.argv[3]

    corpus_files_path = os.path.join(corpus_files_path, project, corpus_lang)
    query_files_path = os.path.join(query_files_path, project, query_lang)
    match_results_path = os.path.join(match_results_path, project, f"{query_lang}__{corpus_lang}")
    query_files = os.listdir(query_files_path)

    # 获取匹配池子
    corpus = read_corpus(corpus_files_path)
    tokenized_corpus = [tokenize_code(doc) for doc in corpus]
    bm25 = BM25Plus(tokenized_corpus)

    # 获取请求
    for query_file in query_files:
        with open(os.path.join(query_files_path, query_file), 'r') as input_file:
            query = input_file.read()

        # 对于每个请求计算前n个匹配结果
        # 放大函数名的权重
        tokenized_query = tokenize_code(query)
        
        # 获取相关性评分
        scores = bm25.get_scores(tokenized_query)
        # 获取最相关的前几个函数定义
        top_n = 10
        match_results_index = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]

        # 如果文件夹不存在，则创建它
        if not os.path.exists(match_results_path):
            os.makedirs(match_results_path)
        
        # 记录匹配结果
        with open(os.path.join(match_results_path, query_file), 'w') as output_file:
            output_file.write("<Target function>\n")
            output_file.write(query)
            output_file.write("\n</Target function>\n\n")
            # for match_result in match_results:
            #     output_file.write(match_result)
            #     output_file.write("\n")
            output_file.write("<Possible matching functions>\n")
            i = 1
            for index in match_results_index:
                output_file.write("<Function {}> \n{}\n</Function {}>\n\n".format(i, corpus[index], i))
                # output_file.write("Score: {}\n".format(scores[index]))
                i += 1
            output_file.write("</Possible matching functions>\n")
                

if __name__ == "__main__" :
    main()