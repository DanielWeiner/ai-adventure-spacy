#!/bin/bash

# Initialize variables with default values
SSH_USER=""
PRIVATE_KEY_FILE=""
SSH_HOST=""
LOCAL_PORT="12049"
TARGET_HOST=""
TARGET_PORT="2049"
USER_COMMAND=""
MOUNT_POINT=""
REMOTE_FOLDER="/"

# Parse named and shorthand parameters
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ssh-user | -u)
      SSH_USER="$2"
      shift 2
      ;;
    --private-key-file | -k)
      PRIVATE_KEY_FILE="$2"
      shift 2
      ;;
    --ssh-host | -h)
      SSH_HOST="$2"
      shift 2
      ;;
    --local-port | -l)
      LOCAL_PORT="$2"
      shift 2
      ;;
    --target-host | -t)
      TARGET_HOST="$2"
      shift 2
      ;;
    --target-port | -p)
      TARGET_PORT="$2"
      shift 2
      ;;
    --command | -c)
      USER_COMMAND="$2"
      shift 2
      ;;
    --mount-point | -m)
      MOUNT_POINT="$2"
      shift 2
      ;;
    --remote-folder | -r)
      REMOTE_FOLDER="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check for missing parameters
if [ -z "$SSH_USER" ] || [ -z "$PRIVATE_KEY_FILE" ] || [ -z "$SSH_HOST" ] || \
   [ -z "$LOCAL_PORT" ] || [ -z "$TARGET_HOST" ] || [ -z "$TARGET_PORT" ] || \
   [ -z "$USER_COMMAND" ] || [ -z "$REMOTE_FOLDER" ]; then
  echo "Usage: $0 [--ssh-user|-u] <ssh_user> [--private-key-file|-k] <private_key_file> [--ssh-host|-h] <ssh_host> [--local-port|-l] <local_port> [--target-host|-t] <target_host> [--target-port|-p] <target_port> [--mount-point|-m] <mount_point> [--remote-folder|-r] <remote_folder> [--command|-c] <user_command>"
  exit 1
fi

is_mounted() {
    mount | awk -v DIR="$1" '{if ($3 == DIR) { exit 0}} ENDFILE{exit -1}'
}

# Function to clean up and exit
cleanup() {
  if mountpoint -q "$MOUNT_POINT"; then
    umount $MOUNT_POINT
  fi

  if [ -e "$CONTROL_SOCKET" ]; then
    ssh -S "$CONTROL_SOCKET" -O exit "$SSH_HOST" > /dev/null 2>&1
    rm -f "$CONTROL_SOCKET"
  fi

  exit 0
}

# Trap signals for cleanup
trap 'cleanup' INT TERM EXIT

# Create a unique control socket
CONTROL_SOCKET="/tmp/ssh_tunnel_$RANDOM"

mkdir -p "$HOME/.ssh"
touch "$HOME/.ssh/known_hosts"

# Check if the fingerprint is already in known_hosts
if ! ssh-keygen -F "$SSH_HOST" -f "$HOME/.ssh/known_hosts" >/dev/null; then
  # Add remote host's fingerprint to known_hosts
  ssh-keyscan -H "$SSH_HOST" >> ~/.ssh/known_hosts
fi

# Open the SSH tunnel in the background
ssh -4 -M -S "$CONTROL_SOCKET" -f -N -L "$LOCAL_PORT:$TARGET_HOST:$TARGET_PORT" -i "$PRIVATE_KEY_FILE" "$SSH_USER@$SSH_HOST"

if ! [ -z "$MOUNT_POINT" ]; then
  mkdir -p "$MOUNT_POINT"
  mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport,port="$LOCAL_PORT" -w "127.0.0.1:$REMOTE_FOLDER" "$MOUNT_POINT"
fi

# Run the user-provided command locally
eval "$USER_COMMAND"
