import os
import yaml

path = os.path.dirname(os.path.abspath(__file__))

if os.path.isfile(os.path.join(path, 'config.yml')):
    with open(os.path.join(path, 'config.yml'), 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)
else:
    with open(os.path.join(path, "default.yml"), 'r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)

if os.path.isfile(os.path.join(path, f'{cfg["language"]}.yml')):
    with open(os.path.join(path, f'{cfg["language"]}.yml')) as ymlfile:
        lang = yaml.safe_load(ymlfile)
else:
    print("Language File missing")
    exit()
