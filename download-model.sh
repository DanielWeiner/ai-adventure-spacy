#!/bin/bash

set -euxo pipefail

AMR_MODEL_NAME=parse_xfm_bart_large-v0_1_0
AMR_MODEL_URL="https://github.com/bjascob/amrlib-models/releases/download/$AMR_MODEL_NAME/model_$AMR_MODEL_NAME.tar.gz"
AMR_TMP_DIR=/tmp/amr
AMR_TMP_MODEL_FILE="$AMR_TMP_DIR/model.tar.gz"
AMR_TMP_MODEL_DIR="$AMR_TMP_DIR/stog_model"

mkdir -p "$AMR_TMP_DIR"
mkdir -p "$AMR_TMP_MODEL_DIR"

curl -Lo "$AMR_TMP_MODEL_FILE" "$AMR_MODEL_URL"
mkdir -p "$AMR_STOG_DIR"
tar -xzf "$AMR_TMP_MODEL_FILE" -C "$AMR_TMP_MODEL_DIR" --strip-components 1
mv "$AMR_TMP_MODEL_DIR"/* "$AMR_STOG_DIR"
rm -f "$AMR_TMP_MODEL_FILE"
rm -rf "$AMR_TMP_MODEL_DIR"