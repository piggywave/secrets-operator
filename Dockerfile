FROM --platform=${TARGETPLATFORM:-linux/amd64} flant/jq:b6be13d5-musl as libjq

FROM --platform=${TARGETPLATFORM:-linux/amd64} golang:1.20-alpine3.16 as builder

ARG appVersion=v1.3.1

RUN apk --no-cache add git ca-certificates gcc musl-dev libc-dev && \
    git clone --branch v1.3.1 https://github.com/flant/shell-operator.git /app

WORKDIR /app

RUN go mod download

COPY --from=libjq /libjq /libjq

RUN CGO_ENABLED=1 \
    CGO_CFLAGS="-I/libjq/include" \
    CGO_LDFLAGS="-L/libjq/lib" \
    GOOS=linux \
    go build -ldflags="-linkmode external -extldflags '-static' -s -w -X 'github.com/flant/shell-operator/pkg/app.Version=$appVersion'" \
             -tags use_libjq \
             -o shell-operator \
             ./cmd/shell-operator

FROM python:3.10-alpine

ENV ARCH=amd64

RUN apk --no-cache add jq yq bash curl unzip openssl && \
    apk --no-cache add gcc libffi-dev openssl-dev musl-dev && \
    export CRYPTOGRAPHY_DONT_BUILD_RUST=1 && \
    pip install --no-cache-dir ansible_runner==2.2.0 ansible==2.9.27 kubernetes --use-deprecated=legacy-resolver && \
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

WORKDIR /app

COPY --from=builder /app/shell-operator /app/

ADD hooks/00-hook.py /app/hooks/

ADD requirements.txt /app/

RUN pip install -r requirements.txt 

RUN chmod +x -R /app/hooks

ENV SHELL_OPERATOR_WORKING_DIR /app/hooks

ENTRYPOINT ["/app/shell-operator"]

CMD ["start"]