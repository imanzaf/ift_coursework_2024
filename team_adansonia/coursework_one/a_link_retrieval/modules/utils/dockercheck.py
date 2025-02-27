import os

def is_running_in_docker():
    return os.path.exists("/.dockerenv")

if __name__ == "__main__":
    print(is_running_in_docker())