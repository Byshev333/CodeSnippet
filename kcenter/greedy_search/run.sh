# python run.py data/st_data.json data/st_data_20w.json 200000

export http_proxy=http://oversea-squid2.ko.txyun:11080 https_proxy=http://oversea-squid2.ko.txyun:11080 no_proxy=localhost,127.0.0.1,localaddress,localdomain.com,internal,corp.kuaishou.com,test.gifshow.com,staging.kuaishou.com
# python run.py /nlp_group/baixue05/LLM_aries/alignment/datasets/clean/en/cluster/data.json /nlp_group/baixue05/LLM_aries/alignment/datasets/clean/en/cluster/data100w.json
python run.py /nlp_group/suzhenpeng/runing_ct/open_source_data_chinese/chatgpt-client/v2/logic_seek/data_dedup_fout.json /nlp_group/suzhenpeng/runing_ct/open_source_data_chinese/chatgpt-client/v2/logic_seek/data_dedup_fout_3w.json