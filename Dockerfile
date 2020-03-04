ARG ALPINE_VERSION="${ALPINE_VERSION:-3.10}"
ARG PYTHON_VERSION="${PYTHON_VERSION:-3.7}"
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION}

WORKDIR /code

## add a non-root user
ARG USER_ID="${USER_ID:-1000}"
ENV USER_ID=$USER_ID

RUN apk add --no-cache --virtual .build-deps \
        git \
    && rm -rf /var/cache/apk/*

VOLUME ["/code"]

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade  pip \
    && pip install --no-cache-dir --upgrade  -r requirements.txt > /dev/null

ENTRYPOINT ["/entrypoint.sh"]
