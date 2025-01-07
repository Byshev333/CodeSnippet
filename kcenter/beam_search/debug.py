import os
# os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import json
import sys
import numpy as np
from transformers import AutoModel, AutoTokenizer
import torch
from kcenter_beam import *
# from kcenter_greedy import *
from datasets import load_dataset
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm
INPUT_FILE = None
# INPUT_FILE = None

class TextDataset(Dataset):
    def __init__(self, text_list):
        self.text_list = text_list

    def __len__(self):
        return len(self.text_list)

    def __getitem__(self, idx):
        text = self.text_list[idx]
        # 你可以在这里添加文本预处理逻辑，如tokenization
        return text

class Collator():
    def __init__(self,tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, examples):
        text = [ example["text"] for example in examples ]
        proc_data = self.tokenizer(text, return_tensors="pt", truncation=True, padding="longest", max_length=512)
        return proc_data

@torch.no_grad()
def bert_embedding(texts_dataset, batch_size=128, language="en"):
    if language == "en":
        tokenizer = AutoTokenizer.from_pretrained('princeton-nlp/sup-simcse-roberta-base')
        model = AutoModel.from_pretrained('princeton-nlp/sup-simcse-roberta-base',torch_dtype=torch.bfloat16).cuda()
        print("princeton-nlp/sup-simcse-roberta-base")
    if language == "zh":
        tokenizer = AutoTokenizer.from_pretrained('cyclone/simcse-chinese-roberta-wwm-ext')
        model = AutoModel.from_pretrained('cyclone/simcse-chinese-roberta-wwm-ext',torch_dtype=torch.bfloat16).cuda()
        print("cyclone/simcse-chinese-roberta-wwm-ext")
    model.eval()
    cls_hid_li = []
    cls_hid_tmp = []
    i = 0
    collator = Collator(tokenizer)
    texts_dataloader = DataLoader(texts_dataset,collate_fn=collator,batch_size=batch_size, shuffle=False, num_workers=10)
    for encoded_texts in tqdm(texts_dataloader):
        last_hids = model(input_ids=encoded_texts["input_ids"].cuda(), attention_mask=encoded_texts["attention_mask"].cuda())['last_hidden_state']
        cls_hids = last_hids[:,0,:].detach().squeeze()
        cls_hid_tmp.append(cls_hids)
        if (i + 1) % 5 == 0:
            tmp = torch.concat(cls_hid_tmp, dim=0)
            tmp = tmp.cpu()
            cls_hid_li.append(tmp)
            cls_hid_tmp = []
        i += 1
    tmp = torch.concat(cls_hid_tmp, dim=0)
    tmp = tmp.cpu()
    cls_hid_li.append(tmp)
    cls_hid_tmp = []
    cls_hids_tensor = torch.concat(cls_hid_li, dim=0)
    return cls_hids_tensor

# 数据采样
def sample_func(text_list, scores, K, input_file, language):
    global INPUT_FILE
    input_file = input_file + ".pt"
    INPUT_FILE = input_file
    result = []
    if os.path.exists(INPUT_FILE):
        print("LOAD")
        text_embedding = torch.load(INPUT_FILE)
    else:
        print("ENCODING")
        text_embedding = bert_embedding(text_list, 1024, language)
        torch.save(text_embedding, INPUT_FILE)
    
    scores = torch.tensor(scores).cuda()
    result = []
    text_embedding = text_embedding.cuda()
    k_center = kCenterGreedy(text_embedding, scores)
    already_selected = None
    result = k_center.select_batch_(text_embedding, already_selected, K)
    return result


def main(input_file, output_file, K, language):
    data = load_dataset("json", data_files=input_file, split="train")
    instruction_list = []
    scores = []
    for d in data:
        scores.append(d["socre"])
    res = sample_func(text_list=data, scores=scores, K=K, input_file=input_file, language=language)
    print('data length')
    print(len(data))
    
    print('sampling data:')
    print(len(res))
    data_li = []
    for index in res:
        index = int(index)
        row = data[index]
        row = json.dumps(row, ensure_ascii=False) + "\n"
        data_li.append(row)

    with open(output_file, "w") as f:
        f.writelines(data_li)

if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    K = int(float(sys.argv[3])) * 10000
    language = sys.argv[4]

    # input_file = "/nlp_group/suzhenpeng/MetaDataPipeline/MoDS/k-center-beam/lt3.json"
    # output_file = "/nlp_group/suzhenpeng/MetaDataPipeline/MoDS/k-center-beam/lt3_out.json"
    # K = 100
    # language = "en"

    main(input_file, output_file, K, language)
