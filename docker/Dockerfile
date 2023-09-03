FROM public.ecr.aws/lambda/python:3.11 AS deps
ENV LAMBDA_TASK_ROOT=/var/task
ENV AMR_MODEL_NAME=parse_xfm_bart_large-v0_1_0
ENV AMR_MODEL_FILE=model_${AMR_MODEL_NAME}.tar.gz
ENV AMR_MODEL_URL=https://github.com/bjascob/amrlib-models/releases/download/${AMR_MODEL_NAME}/${AMR_MODEL_FILE}

# download AMR model and install it
RUN yum install -y tar gzip
RUN curl -Lo ${AMR_MODEL_FILE} ${AMR_MODEL_URL}
RUN mkdir -p ${LAMBDA_TASK_ROOT}/amrlib/data/model_stog/
RUN tar -xzf ${AMR_MODEL_FILE} -C ${LAMBDA_TASK_ROOT}/amrlib/data/model_stog/ --strip-components 1
RUN rm -f ${AMR_MODEL_FILE}
RUN yum remove -y tar gzip

# download python dependencies
RUN --mount=type=cache,target=/root/.cache/pip pip install -U pip setuptools wheel
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN --mount=type=cache,target=/root/.cache/pip pip install -U -r requirements.txt

FROM deps
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface/hub
# preload facebook/bart-large (avoids doing it at runtime and writing to disk)
RUN python -c "import huggingface_hub; huggingface_hub.snapshot_download('facebook/bart-large', allow_patterns=['*.txt', '*.json'])"

# update transformers cache (avoids doing it at runtime and writing to disk)
RUN python -c "from transformers.utils.hub import move_cache; move_cache()"
ENV TRANSFORMERS_OFFLINE=1
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY lambda-layer/ /opt/
RUN chmod +x /opt/extensions/self-invoke-on-shutdown
RUN chmod +x /opt/self-invoke-on-shutdown/extension.py
CMD [ "lambda_function.handler" ]