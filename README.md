# secrets-operator

A ssh/keypaire generates secret based on `shell-operator`

# usage
1. create crds: `kubectl apply -f deploy/crds.yaml` 
2. start operator, please build image firstly `kubectl apply -f deploy/pod.yaml`
3. create cr `kubectl apply -f deploy/example.yaml` 