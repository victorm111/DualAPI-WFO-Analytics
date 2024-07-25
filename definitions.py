import os


def setup_env():
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))  # This is your Project Root
    CONFIG_PATH = os.path.join(ROOT_DIR, "config\\config.yml")
    print('definitions.py root dir:', ROOT_DIR)
    print('definitions.py CONFIG dir:', CONFIG_PATH)
    # set the env variables
    os.environ["ROOT_DIR"] = ROOT_DIR
    os.environ["CONFIG_PATH"] = CONFIG_PATH
    return