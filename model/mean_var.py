#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''=================================================
@Author  :   baixue
@Date    :   2025/01/07 11:26:29
@Desc    :   计算模型参数的均值和方差
================================================='''


import transformers
from transformers import AutoModel
import torch
import json


def main(save_path,model_path):
    # model  = AutoModel.from_pretrained(pretrained_model_name_or_path="prajjwal1/bert-tiny")
    model = transformers.LlamaForCausalLM.from_pretrained(model_path, device_map="auto")
    parameters_dict = {}
    for name, parameters in model.named_parameters():
        mean = torch.mean(parameters)
        var = torch.var(parameters)
        parameters_dict[name] = [mean.cpu().item(),var.cpu().item()]
        # print(name)
    with open(save_path,"w") as f:
        json.dump(parameters_dict,f,indent=4)


if __name__ == "__main__":
    save_path ="ours_13bv1_394k.weight"
    model_path="/nlp_group/glb/Llama-hybrid-parallelism/llmbenchmark_v1/Llama/pretrain/13b_v0_lr4_22_dywd_v1_csharp128k_dataratio1_alibi_skip_394k_401k/save/iter_0394000/hf_bin"
    main(save_path, model_path)

    # save_path ="llama.weight"
    # model_path="/nlp_group/decapoda-research/llama-13b-hf"
    # main(save_path,model_path)
