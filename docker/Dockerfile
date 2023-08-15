FROM python:3.11-slim
WORKDIR /home/app
ENV VIRTUAL_ENV=/opt/venv
RUN --mount=type=cache,target=/home/app/.venv python -m venv $VIRTUAL_ENV
ENV PATH="$VITRUAL_ENV/bin:$PATH"
RUN --mount=type=cache,target=/root/.cache/pip --mount=type=cache,target=/home/app/.venv pip install -U pip setuptools wheel
RUN --mount=type=cache,target=/root/.cache/pip --mount=type=cache,target=/home/app/.venv pip install -U spacy==3.4.4
RUN --mount=type=cache,target=/root/.cache/pip --mount=type=cache,target=/home/app/.venv python -m spacy download en_core_web_trf
COPY requirements.txt /home/app/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip --mount=type=cache,target=/home/app/.venv pip install -U -r requirements.txt
COPY src/ /home/app/src/
CMD [ "python", "-u", "src/main.py" ]