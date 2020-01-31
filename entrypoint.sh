#!/bin/sh

if [ "$(id -u)" = 0 ]; then
  # USER_ID defaults to 1000 (Dockerfile)
  adduser  -u "$USER_ID" -s /bin/false -D staff &> /dev/null
  exec python docker_image_check.py $@
fi

exec $@
