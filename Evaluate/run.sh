# ./run.sh function_pair_folder_path  target_llm_name dependencies_folder_path

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 function_pair_folder_path  target_llm_name dependencies_folder_path"
    exit 1
fi

# translate function pairs from target LLM
python3 translate_throughLLM.py $1 translate_result $2 $3

# run unit-test
python3 auto_test_rust.py translate_result test_result $2 $1 $3

# calculte the pass@1 of test_resut of target LLM
python3 cnt_success.py test_result $2