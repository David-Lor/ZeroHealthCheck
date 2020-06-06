#!/bin/bash

docker_cmd=(
  "useradd -ms /bin/bash user && su user && cd /home/user &&"
  "git clone https://github.com/David-Lor/ZeroHealthCheck && cd ZeroHealthCheck &&"
  "pip install --user -r requirements.txt && pip install --user pyinstaller &&"
  "make build-binary && mv dist/zerohc /dist/"
)

set -ex

docker run --rm -v "$(pwd)/dist:/dist" python:3.8 bash -c "${docker_cmd[*]}"

