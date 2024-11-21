# check the nums of argument
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 project project_langs"
    exit 1
fi

# extract funciton
python extract_function.py $1
echo "Successfully extract function"

# get function with test case
python rust_extract_unitTest_dependency.py $1 rust
echo "Successfully get function with test case"

# get potential function pair
for target in $2
do
    python match_function_throughBm25.py $1 $target rust 
done
echo "Successfully extract potential function pair"

# match function through LLM
python match_function_throughLLM.py potential_function_pair function_pair_with_identical_functionality $1
echo "Successfully get function pari with identical functionality"

# remove None function pair
python remove_None.py $1
echo "Successfully remove None function pair"

# get function pair's dependencies
for target in $2
do
    lang_pair="rust__${target}"
    python rust_extract_dependency.py $1 $lang_pair rust
done
echo "Successfully get function pair's dependencies"