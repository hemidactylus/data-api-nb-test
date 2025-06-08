#!/usr/bin/env bash

set -euo pipefail

sudo apt update
sudo apt install -y git fuse3

git clone https://github.com/hemidactylus/data-api-nb-test.git

curl -L -O https://github.com/nosqlbench/nosqlbench/releases/latest/download/nb5
chmod +x nb5

./nb5 --version

touch EC2_PROVISION_COMPLETE
