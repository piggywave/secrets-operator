FROM ghcr.io/flant/shell-operator:latest as shell-operator

FROM python:3.10-alpine

ENV ARCH=amd64

RUN apk --no-cache add jq yq bash curl tini unzip openssl && \
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

COPY --from=shell-operator /shell-operator /app/
COPY --from=shell-operator /frameworks /app/
COPY --from=shell-operator /shell_lib.sh /app/

ADD hooks/00-hook.py /app/hooks/

ADD requirements.txt /app/

RUN pip install -r requirements.txt 

RUN chmod +x -R /app/hooks

ENV SHELL_OPERATOR_WORKING_DIR /app/hooks

ENTRYPOINT ["/sbin/tini", "--", "/app/shell-operator"]

CMD ["start"]