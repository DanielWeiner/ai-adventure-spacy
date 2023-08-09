FROM python:3.11-slim AS base-spacy
SHELL [ "/bin/bash", "-c" ]
COPY ./ /home/app
WORKDIR /home/app
RUN python -m venv .venv
RUN source .venv/bin/activate
RUN --mount=type=cache,target=/root/.cache/pip pip install -U pip setuptools wheel
RUN --mount=type=cache,target=/root/.cache/pip pip install -U spacy
RUN --mount=type=cache,target=/root/.cache/pip python -m spacy download en_core_web_trf

FROM python:3.11-slim AS build
SHELL [ "/bin/bash", "-c" ]
COPY --from=base-spacy /home/app/.venv /home/app/.venv
COPY . /home/app
WORKDIR /home/app
RUN source .venv/bin/activate
RUN --mount=type=cache,target=/root/.cache/pip pip install -U -r requirements.txt

FROM build
WORKDIR /home/app
RUN chmod +x /home/app/docker/entrypoint.sh
ENTRYPOINT [ "/home/app/docker/entrypoint.sh" ]