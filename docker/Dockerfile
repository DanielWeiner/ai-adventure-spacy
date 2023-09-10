# syntax=docker/dockerfile:1-labs

FROM public.ecr.aws/lambda/python:3.11 AS base

RUN yum -y update
RUN yum -y install libgomp gperftools-libs
RUN curl -Lo sparsehash-devel.rpm https://dl.fedoraproject.org/pub/epel/7/x86_64/Packages/s/sparsehash-devel-1.12-3.el7.x86_64.rpm
RUN yum -y install sparsehash-devel.rpm
RUN rm -f sparsehash-devel.rpm

FROM base AS fast-align

RUN yum -y groupinstall "Development Tools" 
RUN yum -y install git cmake

RUN git clone https://github.com/clab/fast_align fast_align_src
RUN cd fast_align_src && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make
RUN mkdir fast_align
RUN mv fast_align_src/build/atools fast_align_src/build/fast_align fast_align_src/build/force_align.py fast_align

FROM base AS base-python

ARG TRANSFORMERS_CACHE
ARG AMR_ROOT_DIR

ENV TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE}
ENV AMR_STOG_DIR="${AMR_ROOT_DIR}/amrlib/data/model_stog"

COPY --from=fast-align /var/task/fast_align /var/task/fast_align
ENV FABIN_DIR=/var/task/fast_align

# download python dependencies
RUN --mount=type=cache,target=/root/.cache/pip pip install -U pip setuptools wheel
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN --mount=type=cache,target=/root/.cache/pip pip install -U -r requirements.txt

FROM base-python AS transformers-cache

ARG MOUNT_POINT
ARG REMOTE_FOLDER

# download AMR model and install it
RUN yum -y install tar gzip openssh-clients nfs-utils

COPY mount-efs.sh mount-efs.sh
COPY download-model.sh download-model.sh
RUN chmod +x download-model.sh
RUN chmod +x mount-efs.sh

COPY initialize_cache.py initialize_cache.py

RUN --security=insecure \
    --mount=type=secret,id=SSH_HOST \
    --mount=type=secret,id=SSH_USER \
    --mount=type=secret,id=SSH_KEY \
    --mount=type=secret,id=EFS_HOST \
    ./mount-efs.sh \
        --private-key-file "/run/secrets/SSH_KEY" \
        --ssh-host         "$(cat /run/secrets/SSH_HOST)" \
        --ssh-user         "$(cat /run/secrets/SSH_USER)" \
        --target-host      "$(cat /run/secrets/EFS_HOST)" \
        --mount-point      "${MOUNT_POINT}" \
        --remote-folder    "${REMOTE_FOLDER}" \
        --command          "./download-model.sh && python initialize_cache.py"

FROM base-python AS main

COPY --from=transformers-cache /var/lang/lib/python3.11/site-packages/amrlib/data/model_aligner_faa/ /var/lang/lib/python3.11/site-packages/amrlib/data/model_aligner_faa/

ENV TRANSFORMERS_OFFLINE=1

COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY lambda-layer/ /opt/
RUN chmod +x /opt/extensions/self-invoke-on-shutdown
RUN chmod +x /opt/self-invoke-on-shutdown/extension.py
CMD [ "lambda_function.handler" ]

FROM main AS dev
ARG AMR_ROOT_DIR
ARG TRANSFORMERS_CACHE
COPY --from=transformers-cache ${TRANSFORMERS_CACHE} ${TRANSFORMERS_CACHE}
COPY --from=transformers-cache "${AMR_ROOT_DIR}/amrlib/data/model_stog" "${AMR_ROOT_DIR}/amrlib/data/model_stog"