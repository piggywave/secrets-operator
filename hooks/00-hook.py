#!/usr/bin/env python3

import sys, base64
import rsa
from kubernetes import config, client
from typing import List


def rsa_gen(name: str, namespace: List[str], length: int):
    config.load_config()

    pub, pri = rsa.newkeys(length)

    obj = client.V1Secret(api_version="v1", metadata={"name": name, "namespace": namespace})
    obj.data = {
        "public": base64.b64encode(pub.save_pkcs1()).decode(),
        "private": base64.b64encode(pri.save_pkcs1()).decode()
    }

    v1 = client.CoreV1Api()
    try:
        v1.create_namespaced_secret(namespace=namespace, body=obj)
    except client.ApiException as e:
        if e.status == 409:
            print("%s/%s already exists".format(namespace, name))
        else:
            print(e)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        print('{"configVersion":"v1", "onStartup": 1}')
    else:
        rsa_gen("test", "default", 2048)


if __name__ == '__main__':
    main()
