# syntax=docker/dockerfile:1-labs
FROM public.ecr.aws/lambda/python:3.11 AS deps

ARG AMR_ROOT_DIR
ARG TRANSFORMERS_CACHE
ARG SSH_KEY
ARG MOUNT_POINT
ARG REMOTE_FOLDER
ARG SSH_HOST
ARG SSH_USER
ARG EFS_HOST

ENV TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE}
ENV AMR_STOG_DIR="${AMR_ROOT_DIR}/amrlib/data/model_stog"

# download AMR model and install it
RUN yum install -y tar gzip openssh-clients nfs-utils

COPY mount-efs.sh mount-efs.sh
COPY download-model.sh download-model.sh
RUN chmod +x download-model.sh
RUN chmod +x mount-efs.sh

# run in a subshell to prevent the key from being logged
RUN bash -c "echo \"\$SSH_KEY\""

RUN --security=insecure bash -c "echo \"\$SSH_KEY\"" > "/tmp/key.pem" && \
    chmod 400 "/tmp/key.pem" && \
    ./mount-efs.sh \
        --private-key-file "/tmp/key.pem" \
        --ssh-host         "${SSH_HOST}" \
        --ssh-user         "${SSH_USER}" \
        --target-host      "${EFS_HOST}" \
        --mount-point      "${MOUNT_POINT}" \
        --remote-folder    "${REMOTE_FOLDER}" \
        --command          "./download-model.sh" && \ 
    rm -f "/tmp/key.pem"

# download python dependencies
RUN --mount=type=cache,target=/root/.cache/pip pip install -U pip setuptools wheel
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN --mount=type=cache,target=/root/.cache/pip pip install -U -r requirements.txt

# preload facebook/bart-large (avoids doing it at runtime and writing to disk)
RUN --security=insecure bash -c "echo \"\$SSH_KEY\"" > "/tmp/key.pem" && \ 
    chmod 400 "/tmp/key.pem" && \
    ./mount-efs.sh \
        --private-key-file "/tmp/key.pem" \
        --ssh-host         "${SSH_HOST}" \
        --ssh-user         "${SSH_USER}" \
        --target-host      "${EFS_HOST}" \
        --mount-point      "${MOUNT_POINT}" \
        --remote-folder    "${REMOTE_FOLDER}" \
        --command          "python -c \"import huggingface_hub; from transformers.utils.hub import move_cache; huggingface_hub.snapshot_download('facebook/bart-large', allow_patterns=['*.txt', '*.json']); move_cache()\"" && \
    rm -f "/tmp/key.pem"

RUN yum remove --skip-broken -y tar openssh-clients nfs-utils

FROM deps
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY lambda-layer/ /opt/
RUN chmod +x /opt/extensions/self-invoke-on-shutdown
RUN chmod +x /opt/self-invoke-on-shutdown/extension.py
CMD [ "lambda_function.handler" ]