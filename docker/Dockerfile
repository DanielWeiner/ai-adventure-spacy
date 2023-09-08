# syntax=docker/dockerfile:1-labs

FROM public.ecr.aws/lambda/python:3.11 AS fast_align

RUN yum -y groupinstall "Development Tools" 
RUN yum install -y libgomp gperftools-devel git cmake
RUN curl -Lo sparsehash-devel.rpm https://dl.fedoraproject.org/pub/epel/7/x86_64/Packages/s/sparsehash-devel-1.12-3.el7.x86_64.rpm
RUN yum -y install sparsehash-devel.rpm

RUN git clone https://github.com/clab/fast_align fast_align_src
RUN cd fast_align_src && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make
RUN mkdir fast_align
RUN mv fast_align_src/build/atools fast_align_src/build/fast_align fast_align_src/build/force_align.py fast_align
RUN rm -rf fast_align_src

FROM public.ecr.aws/lambda/python:3.11

ARG AMR_ROOT_DIR
ARG TRANSFORMERS_CACHE
ARG MOUNT_POINT
ARG REMOTE_FOLDER

ENV TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE}
ENV AMR_STOG_DIR="${AMR_ROOT_DIR}/amrlib/data/model_stog"

# download AMR model and install it
RUN yum install -y tar gzip openssh-clients nfs-utils libgomp gperftools-devel
RUN curl -Lo sparsehash-devel.rpm https://dl.fedoraproject.org/pub/epel/7/x86_64/Packages/s/sparsehash-devel-1.12-3.el7.x86_64.rpm
RUN yum -y install sparsehash-devel.rpm
RUN rm -f sparsehash-devel.rpm

COPY --from=fast_align /var/task/fast_align /var/task/fast_align
ENV FABIN_DIR=/var/task/fast_align

COPY mount-efs.sh mount-efs.sh
COPY download-model.sh download-model.sh
RUN chmod +x download-model.sh
RUN chmod +x mount-efs.sh

RUN --security=insecure \
    --mount=type=secret,id=SSH_HOST \
    --mount=type=secret,id=SSH_USER \
    --mount=type=secret,id=SSH_KEY \
    --mount=type=secret,id=EFS_HOST \
    cat /run/secrets/SSH_KEY > "/tmp/key.pem" && \
    chmod 400 "/tmp/key.pem" && \
    ./mount-efs.sh \
        --private-key-file "/tmp/key.pem" \
        --ssh-host         "$(cat /run/secrets/SSH_HOST)" \
        --ssh-user         "$(cat /run/secrets/SSH_USER)" \
        --target-host      "$(cat /run/secrets/EFS_HOST)" \
        --mount-point      "${MOUNT_POINT}" \
        --remote-folder    "${REMOTE_FOLDER}" \
        --command          "./download-model.sh" && \ 
    rm -f "/tmp/key.pem"

# download python dependencies
RUN --mount=type=cache,target=/root/.cache/pip pip install -U pip setuptools wheel
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN --mount=type=cache,target=/root/.cache/pip pip install -U -r requirements.txt

COPY initialize_cache.py initialize_cache.py

# preload facebook/bart-large (avoids doing it at runtime and writing to disk)
RUN --security=insecure \
    --mount=type=secret,id=SSH_HOST \
    --mount=type=secret,id=SSH_USER \
    --mount=type=secret,id=SSH_KEY \
    --mount=type=secret,id=EFS_HOST \
    cat /run/secrets/SSH_KEY > "/tmp/key.pem" && \ 
    chmod 400 "/tmp/key.pem" && \
    ./mount-efs.sh \
        --private-key-file "/tmp/key.pem" \
        --ssh-host         "$(cat /run/secrets/SSH_HOST)" \
        --ssh-user         "$(cat /run/secrets/SSH_USER)" \
        --target-host      "$(cat /run/secrets/EFS_HOST)" \
        --mount-point      "${MOUNT_POINT}" \
        --remote-folder    "${REMOTE_FOLDER}" \
        --command          "python initialize_cache.py" && \
    rm -f "/tmp/key.pem"

RUN yum remove --skip-broken -y tar openssh-clients nfs-utils
RUN rm -f download-model.sh initialize_cache.py mount-efs.sh

ENV TRANSFORMERS_OFFLINE=1

COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY lambda-layer/ /opt/
RUN chmod +x /opt/extensions/self-invoke-on-shutdown
RUN chmod +x /opt/self-invoke-on-shutdown/extension.py
CMD [ "lambda_function.handler" ]