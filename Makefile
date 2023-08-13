.PHONY: image
image:
	docker build -t piggywave/shell-operator:v1 .

.PHONY: load
load: image
	kind load docker-image piggywave/shell-operator:v1