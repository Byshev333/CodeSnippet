import json

path = "new_gpt_gen/res_data_ours.json"

with open(path,"r") as f:
    data = f.readlines()

index = 0
new_data = []

for row in data:
    row_load = json.loads(row)
    row_load["id"] = str(index)
    row = json.dumps(row_load,ensure_ascii=False) + "\n"
    new_data.append(row)
    index += 1

save_path = path.replace(".json","_ids.json")

with open(save_path,"w") as f:
    f.writelines(new_data)
