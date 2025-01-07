set -xv
gpu_nums=100
#处理数据的脚本
code=$3
#临时文件存储目录
tmp_dir=$4
#输入文件
input_path=$1
input_file=${input_path##*/}
#输出文件
output_file=$2

num=`wc -l $input_path|cut -d' ' -f1`
per_num=`expr $num / $gpu_nums + 1`
rm -rf $tmp_dir
mkdir $tmp_dir
split -l $per_num  -a 3 $input_path $tmp_dir/${input_file}.part -d
for i in `seq 1 $gpu_nums`
do
    i=`expr $i - 1`
    index=$i
    if [ $i -lt 10 ]
    then
        index=00$i
    elif [ $i -lt 100 ]
    then
        index=0$i
    else
        index=$i
    fi
    python $code  $tmp_dir/${input_file}.part$index   $tmp_dir/${input_file}.out${index} &

done

wait

cat $tmp_dir/${input_file}.out* |LC_ALL=C sort -u > $output_file


