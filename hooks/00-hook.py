#!/usr/bin/env python3

import sys, base64, os, json
import rsa
from kubernetes import config, client
from typing import List


rsa_hook = '''
{
  "configVersion":"v1",
  "kubernetes":[{
    "name": "monitoring rsa",
    "apiVersion": "stable.example.com/v1",
    "kind": "RSA",
    "executeHookOnEvent":["Added", "Deleted"],
    "executeHookOnSynchronization":false
  }]
}
'''

def rsa_gen(name: str, namespace: List[str], length: int, mode: str, pubkey: str, prikey: str):
    config.load_config()
    v1 = client.CoreV1Api()
    match mode:
        case "Added":
            pub, pri = rsa.newkeys(length)
            obj = client.V1Secret(api_version="v1", metadata={"name": name})
            obj.data = {
                pubkey: base64.b64encode(pub.save_pkcs1()).decode(),
                prikey: base64.b64encode(pri.save_pkcs1()).decode()
            }
            for ns in namespace:
                try:
                    obj.namespace = ns
                    v1.create_namespaced_secret(namespace=ns, body=obj)
                except client.ApiException as e:
                    if e.status == 409:
                        log = "%s/%s already exists".format(ns, name)
                        print(log)
                    else:
                        print(e)
        case "Deleted":
            for ns in namespace:
                try:
                    v1.delete_namespaced_secret(name=name, namespace=ns)
                except client.ApiException as e:
                    if e.status == 404:
                        log = "%s/%s does not exist".format(ns, name)
                        print(log)
                    else:
                        print(e)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        print(rsa_hook)
        return
    else:
        with open(os.environ.get("BINDING_CONTEXT_PATH"), 'r') as f:
            data = json.load(f)
            for event in data:
                event_type = event['watchEvent']
                name = event['object']['spec']['name']
                namespace = event['object']['spec']['namespace']
                length = event['object']['spec']['length']
                publickey = event['object']['spec']['publicKey']
                privatekey = event['object']['spec']['privateKey']
                rsa_gen(name, namespace, length, event_type, publickey, privatekey)

if __name__ == '__main__':
    main()
