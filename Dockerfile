FROM golang:1.17-alpine3.16

ARG appVersion=latest

RUN apk --no-cache add git ca-certificates && \
    git clone --branch v1.0.0-beta.5 https://github.com/flant/shell-operator.git /go/src/github.com/flant/shell-operator

RUN go get -d github.com/flant/shell-operator/...

WORKDIR /go/src/github.com/flant/shell-operator

RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w -X 'github.com/flant/shell-operator/pkg/app.Version=$appVersion'" -o shell-operator ./cmd/shell-operator

FROM python:3.10-alpine

ENV ARCH=amd64

RUN apk --no-cache add jq yq bash curl unzip openssl && \
    apk --no-cache add gcc libffi-dev openssl-dev musl-dev && \
    export CRYPTOGRAPHY_DONT_BUILD_RUST=1 && \
    pip install --no-cache-dir ansible_runner==2.2.0 ansible==2.9.27 kubernetes rsa --use-deprecated=legacy-resolver && \
    apk del gcc libffi-dev openssl-dev musl-dev && \
    if [[ $(arch) == aarch64* ]]; then ARCH=arm64; fi && \
    wget https://get.helm.sh/helm-v3.9.0-linux-${ARCH}.tar.gz && \
    tar -zxf helm-v3.9.0-linux-${ARCH}.tar.gz && \
    mv linux-${ARCH}/helm /bin/helm && \
    rm -rf *linux-${ARCH}* && \
    chmod +x /bin/helm && \
    wget https://storage.googleapis.com/kubernetes-release/release/v1.23.7/bin/linux/${ARCH}/kubectl -O /bin/kubectl && \
    chmod +x /bin/kubectl && \
    ln -s /bin/kubectl /usr/local/bin/kubectl && \
    ln -s /bin/helm /usr/local/bin/helm

COPY --from=0 /go/src/github.com/flant/shell-operator/shell-operator /

WORKDIR /app

COPY . .

ENV SHELL_OPERATOR_WORKING_DIR /app/hooks

# ENTRYPOINT ["/shell-operator"]

# CMD ["start"]