import os
# os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import json
import sys
import numpy as np
from transformers import AutoModel, AutoTokenizer
import torch
from kcenter_greedy import *
from datasets import load_dataset
from tqdm import tqdm
INPUT_FILE = None
# INPUT_FILE = None

@torch.no_grad()
def bert_embedding(texts,batch=128):
    tokenizer = AutoTokenizer.from_pretrained('cyclone/simcse-chinese-roberta-wwm-ext')
    model = AutoModel.from_pretrained('cyclone/simcse-chinese-roberta-wwm-ext').cuda()
    # tokenizer = AutoTokenizer.from_pretrained('princeton-nlp/sup-simcse-bert-base-uncased')
    # model = AutoModel.from_pretrained('princeton-nlp/sup-simcse-bert-base-uncased').cuda()
    model.eval()
    cls_hid_li = []
    i= 0
    l = len(texts)
    while i < len(texts):
        sub_texts = texts[i:i+batch]
        encoded_texts = tokenizer(sub_texts,return_tensors="pt",truncation=True,padding="longest",max_length=256)
        last_hids = model(input_ids=encoded_texts["input_ids"].cuda(),
                          attention_mask=encoded_texts["attention_mask"].cuda())['last_hidden_state']
        cls_hids = last_hids[:,0,:].detach().cpu().squeeze()
        cls_hid_li.append(cls_hids)
        i+= batch
        print(f"{i}/{l}")
    cls_hids_tensor = torch.concat(cls_hid_li, dim=0)
    return cls_hids_tensor

# 数据采样
def sample_func(text_list, K, input_file):
    global INPUT_FILE
    input_file = input_file + ".pt"
    INPUT_FILE = input_file
    result = []
    if os.path.exists(INPUT_FILE):
        print("LOAD")
        text_embedding = torch.load(INPUT_FILE)
    else:
        print("ENCODING")
        text_embedding = bert_embedding(text_list)
        torch.save(text_embedding, INPUT_FILE)
    
    result = []
    # text_embedding = np.array(text_embedding.cpu())
    text_embedding = text_embedding.cuda()
    k_center = kCenterGreedy(text_embedding)
    already_selected = None
    result = k_center.select_batch_(text_embedding, already_selected, K)
    return result


def main(input_file, output_file, K):
    data = []
    with open(input_file,"r") as f:
        data = f.readlines()
    data = [ json.loads(row) for row in tqdm(data) ]
    instruction_list = []
    for d in data:
        q = ""
        for r in d["text"]:
            cq = r["question"]
            q += f"{cq}\n"
        instruction_list.append(q)
    print(len(instruction_list))
    res = sample_func(text_list = instruction_list, K = K, input_file=input_file)
    print('data length')
    print(len(data))
    
    print('sampling data:')
    print(len(res))
    data_li = []
    for index in res:
        index = int(index)
        row = data[index]
        row = json.dumps(row, ensure_ascii = False) + "\n"
        data_li.append(row)

    with open(output_file, "w") as f:
        f.writelines(data_li)

if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    # K = int(float(sys.argv[3]))
    # K = 1000000
    K = 30000
    main(input_file, output_file, K)


