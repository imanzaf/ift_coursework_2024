from flask_sqlalchemy import SQLAlchemy
import yaml
import os

# load config
def load_config():
    # Absolute path to your conf.yaml file
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'coursework_one'))
    config_path = os.path.join(project_root, 'config', 'conf.yaml')

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as config_file:
        return yaml.safe_load(config_file)

# get config
config = load_config()

# initialize db
db = SQLAlchemy()

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = config['database']['uri']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config['database']['track_modifications']
    db.init_app(app)
