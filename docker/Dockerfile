FROM public.ecr.aws/lambda/python:3.11
ENV $LAMBDA_TASK_ROOT=/var/task
RUN --mount=type=cache,target=/root/.cache/pip pip install -U pip setuptools wheel
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN --mount=type=cache,target=/root/.cache/pip pip install -U -r requirements.txt
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
CMD [ "lambda_function.handler" ]