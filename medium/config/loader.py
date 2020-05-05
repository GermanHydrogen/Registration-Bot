import os
import yaml

path = os.path.dirname(os.path.abspath(__file__))

if os.path.isfile(path + '/config.yml'):
    with open(path + "/config.yml", 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
else:
    print("Please add config.yml to the dir")
    exit()

if not cfg["token"] and cfg["role"] and cfg["language"]:
    print("No valid token in config.yml")
    exit()

if os.path.isfile(path + f'/{cfg["language"]}.yml'):
    with open(path + f'/{cfg["language"]}.yml') as ymlfile:
        lang = yaml.safe_load(ymlfile)
else:
    print("Language File missing")
    exit()
