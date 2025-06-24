#!/usr/bin/env bash

set -euo pipefail

sudo apt update
sudo apt install -y git fuse3 rsync

git clone https://github.com/hemidactylus/data-api-nb-test.git

# TODO: reinstate once the symlink issue with 5.21.8-release is fixed:
# https://github.com/nosqlbench/nosqlbench/releases/latest/download/nb5
curl -L -O https://github.com/nosqlbench/nosqlbench/releases/download/5.21.7-release/nb5
chmod +x nb5

touch EC2_PROVISION_COMPLETE
