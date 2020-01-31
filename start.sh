#!/bin/bash

set -Eeuo pipefail

docker-compose -p docker build

docker-compose -p docker run --rm image_check "$@"  #  | vim -
