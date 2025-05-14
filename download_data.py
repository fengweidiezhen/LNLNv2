from oss_utils import *

t = TencentOss()

t.download_file(cos_key="nuna_algorithm_simulation_data/chunhaohuang/data.zip", local_file="data.zip")