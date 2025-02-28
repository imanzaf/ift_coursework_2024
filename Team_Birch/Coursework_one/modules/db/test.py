import os


base_dir = os.path.dirname(os.path.abspath(__file__))
print(base_dir)

config_file_path = os.path.join(base_dir, '..', '..', 'coursework_one', 'config', 'conf.yaml')


config_file_path = os.path.normpath(config_file_path)


with open(config_file_path, 'r') as config_file:
    config_data = config_file.read()

print(config_data)
