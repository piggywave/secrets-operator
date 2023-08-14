#!/usr/bin/env python3

import sys, base64, os, json
import rsa
from kubernetes import config, client
from typing import Dict


hooks = '''
{
  "configVersion":"v1",
  "kubernetes":[
    {
        "name": "monitoring rsa",
        "apiVersion": "stable.example.com/v1",
        "kind": "RSA",
        "executeHookOnEvent":["Added", "Deleted"],
        "executeHookOnSynchronization": false
    },
    {
        "name": "monitoring keypair",
        "apiVersion": "stable.example.com/v1",
        "kind": "KeyPair",
        "executeHookOnEvent":["Added", "Deleted"],
        "executeHookOnSynchronization": false
    }
  ]
}
'''

class RSARequest:
    def __init__(self, data: Dict[str, any]) -> None:
        self.mode = data['watchEvent']
        self.name = data['object']['spec']['name']
        self.namespace = data['object']['spec']['namespace']
        self.length = data['object']['spec']['length']
        self.public_key = data['object']['spec']['publicKey']
        self.private_key = data['object']['spec']['privateKey']

    def rsa_gen(self):
        config.load_config()
        v1 = client.CoreV1Api()
        match self.mode:
            case "Added":
                pub, pri = rsa.newkeys(self.length)
                obj = client.V1Secret(api_version="v1", metadata={"name": self.name})
                obj.data = {
                    self.public_key: base64.b64encode(pub.save_pkcs1()).decode(),
                    self.private_key: base64.b64encode(pri.save_pkcs1()).decode()
                }
                for ns in self.namespace:
                    try:
                        obj.namespace = ns
                        v1.create_namespaced_secret(namespace=ns, body=obj)
                    except client.ApiException as e:
                        print(e)
            case "Deleted":
                for ns in self.namespace:
                    try:
                        v1.delete_namespaced_secret(name=self.name, namespace=ns)
                    except client.ApiException as e:
                        print(e)

class KeyPair:
    def __init__(self, data: Dict[str, any]) -> None:
        self.mode = data['watchEvent']
        self.name = data['object']['spec']['name']
        self.namespace = data['object']['spec']['namespace']
        self.pairs = data['object']['spec']['data']

    def keypair_gen(self):
        config.load_config()
        v1 = client.CoreV1Api()
        match self.mode:
            case "Added":
                obj = client.V1Secret(api_version="v1", metadata={"name": self.name})
                obj.data = {}
                for key, value in self.pairs.items():
                    obj.data[key] = base64.b64encode(value.encode()).decode()
                for ns in self.namespace:
                    try:
                        obj.namespace = ns
                        v1.create_namespaced_secret(namespace=ns, body=obj)
                    except client.ApiException as e:
                        print(e)
            case "Deleted":
                for ns in self.namespace:
                    try:
                        v1.delete_namespaced_secret(name=self.name, namespace=ns)
                    except client.ApiException as e:
                        print(e)
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        print(hooks)
        return
    else:
        with open(os.environ.get("BINDING_CONTEXT_PATH"), 'r') as f:
            events = json.load(f)
            for event in events:
                match event['binding']:
                    case "monitoring rsa":
                        rr = RSARequest(event)
                        rr.rsa_gen()
                    case "monitoring keypair":
                        kp = KeyPair(event)
                        kp.keypair_gen()

if __name__ == '__main__':
    main()
