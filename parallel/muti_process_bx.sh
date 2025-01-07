set -xv
cpu_nums=100
#处理数据的脚本
code=clean.py
#临时文件存储目录
tmp_dir=/mmu_nlp_ssd/baixue05/LLM_aries/pretraindata/exercise_data/baiduwenku/data_tmp
#输入文件
input_path=/mmu_nlp_ssd/baixue05/LLM_aries/pretraindata/exercise_data/baiduwenku/data/baiduwenku.json
input_file=${input_path##*/}
output_file=/mmu_nlp_ssd/baixue05/LLM_aries/pretraindata/exercise_data/baiduwenku/data/baiduwenku.clean.json


num=$(wc -l $input_path | awk '{print $1}')
per_num=$((num / cpu_nums + 1))
rm -rf $tmp_dir
mkdir $tmp_dir
split -l $per_num -a 3 -d $input_path $tmp_dir/${input_file}.part

for part_file in $tmp_dir/${input_file}.part*; do
    echo "Processing file: $part_file"
    last_three_digits="${part_file: -3}"
    python -u $code < $part_file > "${part_file}.out$last_three_digits" &
done

wait

cat $tmp_dir/${input_file}.part*.out* |LC_ALL=C sort -u > $output_file