from steps.helpers import read_config

conf = read_config('config.yaml')

print(conf['Step1']['model_name'])