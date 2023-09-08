#!/bin/bash

CURRENT_BUILDER=""

check-builder() {
    local CURRENT_BUILDER=$(docker buildx ls 2>/dev/null | grep '*'| grep -v default | awk '{print $1}')
    local BUILDER_FLAG=""
    
    if [ -z "$CURRENT_BUILDER" ]; then
        return
    fi

    BUILDER_FLAG=$(docker buildx inspect $CURRENT_BUILDER | grep 'Flags:' | grep '\-\-allow-insecure-entitlement security.insecure')

    if [ -z "$BUILDER_FLAG" ]; then
        return
    fi

    echo "$CURRENT_BUILDER"
}

create-builder() {
    docker buildx create --buildkitd-flags '--allow-insecure-entitlement security.insecure' --use
}

set-current-builder() {
    CURRENT_BUILDER=$(check-builder)

    if [ -z "$CURRENT_BUILDER" ]; then
        CURRENT_BUILDER=$(create-builder)
    fi
}

cleanup() {
    if ! [ -z "$CURRENT_BUILDER" ]; then
        docker buildx rm "$CURRENT_BUILDER"
    fi
}

build() {
    if [ -f "./.env" ]; then
        set -a
        source .env
        set +a
    fi

    set-current-builder

    trap 'cleanup' INT TERM EXIT

    docker buildx build \
        --allow security.insecure \
        --build-arg AMR_ROOT_DIR="$AMR_ROOT_DIR" \
        --build-arg TRANSFORMERS_CACHE="$TRANSFORMERS_CACHE" \
        --build-arg MOUNT_POINT="$MOUNT_POINT" \
        --build-arg REMOTE_FOLDER="$REMOTE_FOLDER" \
        --secret id=SSH_KEY \
        --secret id=SSH_HOST \
        --secret id=SSH_USER \
        --secret id=EFS_HOST \
        -t ai-adventure-spacy \
        -f docker/Dockerfile \
        "$@" \
        .
}

(build "$@")