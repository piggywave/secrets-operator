import sys, rsa
from kubernetes import config, client
from typing import List

def rsa_gen(name: str, namespace: List[str], length: int):
    config.load_config()
    

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        print()
        return
    else:
        config.load_config()
    api = client.CustomObjectsApi()


if __name__ == '__main__':
    main()
