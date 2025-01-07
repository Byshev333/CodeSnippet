#!/bin/bash
set -xv
# Machine and process configurations
machine_num=80
num_processes=80
ip_dir=tmp_ip
input_f=all_zlib2.shuf.pdf.meta.100w.shuf
tmp_dir=tmp
input_path=$input_f # Add the correct path to your input file

# Setup directories and touch IP file
mkdir -p ${ip_dir}
touch "${ip_dir}/$MY_NODE_IP"

# Wait for all machines to register
ip_num=$(ls $ip_dir | wc -l)
while [[ "$ip_num" != "$machine_num" ]]; do
    sleep 10s
    ip_num=$(ls $ip_dir | wc -l)
done

# Determine master IP and rank of this node
MASTER_IP=$(ls $ip_dir | sort | head -n 1)
MY_RANK=$(ls $ip_dir | sort | grep -wn "$MY_NODE_IP" | cut -d: -f1)
MY_RANK=$(($MY_RANK - 1))

echo "Master IP: $MASTER_IP"
echo "My Rank: $MY_RANK"
num=$(wc -l $input_f | cut -d' ' -f1)
per_num=$(($num / $machine_num + 1))
# Split input file if this is the master node
if [[ "$MY_NODE_IP" == "$MASTER_IP" ]]; then 
    rm -rf $tmp_dir
    mkdir $tmp_dir
    split -l $per_num -a 3 -d $input_f $tmp_dir/${input_f}.part
fi

# Wait for split to complete on master before proceeding
sleep 200s

# Calculate number of lines per process
peer_per_num=$(($per_num / $num_processes + 1))

# Format MY_RANK with leading zeros for file naming
printf -v index "%03d" $MY_RANK

# Split the assigned part file for this node
split -l $peer_per_num -a 3 -d $tmp_dir/${input_f}.part$index $tmp_dir/${input_f}.part${index}.${MY_RANK}.subpart

# Process each subpart file with pdf_ocr.py script
for i in $(seq 1 $num_processes); do
    i=$(($i - 1))
    printf -v index2 "%03d" $i
    python pdf_ocr.py  $tmp_dir/${input_f}.part${index}.${MY_RANK}.subpart$index2  $tmp_dir/${input_f}.part${index}.${MY_RANK}.subpart.out.$index2 $peer_per_num &
done

wait # Wait for all background processes to complete

# Concatenate all output files into a final file
cat $tmp_dir/${input_f}.part${index}.${MY_RANK}.subpart.out.* > $tmp_dir/${input_f}.part${index}.${MY_RANK}.final
