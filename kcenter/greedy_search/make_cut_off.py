import json
import re
    
def make_cut_off_data(gpt_path):
    new_data = []
    cut_off_data = []
    cut_off_keys = ["2023年4月"]
    del_keys = ["重写下面这段文本：████"]
    index = 0
    with open(gpt_path, 'r') as f:
        data = f.readlines()
        for row in data:
            row_load = json.loads(row)
            row_load = row_load["data"]
            row_save = json.dumps({"data":row_load,"id":str(index)},ensure_ascii=False) + "\n"
            key = ""
            question_key = ""
            for r in row_load:
                answer = r["answer"].strip()
                key += answer
                question_key += r["question"].strip()
            if any(keyword in question_key for keyword in del_keys):
                print(row_save)
                continue
            if any(keyword in key for keyword in cut_off_keys):
                cut_off_data.append(row_save)
                continue
            new_data.append(row_save)
            index += 1
    
    save_path = gpt_path.replace(".json","_save.json")
    with open(save_path, 'w') as f:
        f.writelines(new_data)

    cut_off_path = gpt_path.replace(".json","_cut_off.json")
    with open(cut_off_path, 'w') as f:
        f.writelines(cut_off_data)

        
if __name__=="__main__":
    gpt_path = "/nlp_group/suzhenpeng/UpcyclingTuning/k_center_data/greedy_search/new_gpt_gen/st_res_mt_gpt_clean_gpt_clean.json"
    make_cut_off_data(gpt_path)