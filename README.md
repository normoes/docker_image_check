# Docker image check

This tool can be used to report unwanted docker images in production environemnts.

A possible scenario is a production envrionment running services within docker containers which should - by security policy - be based on images from specific docker repositories only.


## Use

By default `docker_image_check` returns unwanted images that should not be used by running containers.

Two modes are supported:
* **blacklist**: Images defined in `./images.txt` are considered **bad**.
  - **Returns images found in `images.txt`.**
* **whitelist**: Images defined in `./images.txt` are considered **good**.
  - **Returns images not found in `images.txt`.**

Additional flags:
* `--image-file` to use a configuration file other than `./images.txt`.
* `--layers`show underlying docker image layers.
* `--debug` shows debug logs.

## Configuration

Images are read from `./images.txt` by default. The option `--image-file` can be used to read images from a configuration file other than the default one.

Images in `./images.txt` can be added by:
* full name
* regular expression


Comments in `./images.txt` start with `#`.

Blank lines are ignored.

## Docker

This tool works with the docker unix socket: `unix://var/run/docker.sock`.

When running the tool from within a docker container, it's important to mount the docker unix socket into the container:
```
docker build -t image_check .
docker run --rm -d -v /var/run/docker.sock:/var/run/docker.sock  image_check whitelist
```

You can also use docker-compsoe with the provided `docker-compose.yml` file. The script `start.sh` provides a simple way to start a docker container:
```
./start.sh whitelist
./start.sh whitelist --layers
./start.sh whitelist --debug
```

## Examples

### whitelist
Coming back to the `whitelist` scenario above:
> A possible scenario is a production envrionment running services within docker containers which should - by security policy - be based on images from specific docker repositories only.

* Let's assume that production images should all be part of the `my_company/` docker repository - No other docker repository is allowed.
* Let's also assume you are running the following images in your production environment:
    - `my_company/nginx`
    - `my_company/service`
    - `developer_a/log_converter`
    - `malicious_repo/some_image`
    - `python:3.7-alpine3.10`
* Running `whitelist` mode - Only allow images listed in your `images.txt`.
* This is your `images.txt`:
```
  # comment
  # blank lines are ignored
  my_company/*  
```
* `python app.py whitelst`.
* **Output**:
    ```
      # The output shows all the images (used by running containers) that are not listed in the configuration file.
      INFO:__main__:[whitelist] Bad image found: 'malicious_repo/some_image'.
      INFO:__main__:[whitelist] Bad image found: 'python:3.7-alpine3.10'.
      INFO:__main__:[whitelist] Bad image found: 'developer_a/log_converter'.
      INFO:__main__:[whitelist] Good image found: 'my_company/nginx'.
      INFO:__main__:[whitelist] Good image found: 'my_company/service'.
      malicious_repo/some_image
      python:3.7-alpine3.10
      developer_a/log_converter
    ```

### blacklist
A `blacklist` scenario could look like this:

* Let's assume you are using docker images from  a docker repository `malicious_repo/` that was flagged as malicious by several users - You would like to get a report about docker containers based on docker images from this particular docker repository.
* Let's also assume you are running the following images:
    - `python:3.7-alpine3.10`
    - `malicious_repo/some_image`
* Running `blacklist` mode - Only allow images not listed in your  `images.txt`.
* This is your `images.txt`:
```
  # comment
  # blank lines are ignored
  malicious_repo/*
```
* `python app.py blacklist`.
* **Output**:
    ```
      # The output shows all the images (used by running containers) that are listed in the configuration file.
      INFO:__main__:[blacklist] Bad image found: 'malicious_repo/some_image'.
      INFO:__main__:[blacklist] Good image found: 'python:3.7-alpine3.10'.
      malicious_repo/some_image
    ```
### layers
In addition to the image name it's possible to also return the underlying image layers (sha256 hashes) of the image.

In a later version, this will be used to compare against given docker base image sha256 hashes to make sure the base image used in the `Dockerfile` is the expected one.

For now, when inlcuding the docker image layers:
```
python app.py whitelist --layers
```
a result will look like this:
```
{
  "alpine": [
    "sha256:bcf2f368fe234217249e00ad9d762d8f1a3156d60c442ed92079fb7b120634a1"
  ],
  "some_image": [
    "sha256:0f55ea869d5ef070fb34800d05b6a12a08847c4211a6978edf1747y6c430f799",
    "sha256:08a7b06cc05d97bb40417cf2be53f6017f3d12bd730a5e3f0c2af9qeab2722d4",
    "sha256:b07f62281aacf7922e887d6fe4a73e2599846ba35fb60fa9b84d3bn30a84480c",
    "sha256:d1bcc7cabf25389bf5c5d155f39b6d823393d3b6fd21975dff9423a9ddc6e815",
    "sha256:309c3b3db49b9315d529560f5ad085a0dfd9945262d6d947bcd423385d55c9d7",
    "sha256:b45e998698658e2641524a1e05dac81553539f3a005b0f5cc7bc41edb78d3278",
    "sha256:f238e063ec4595842f93f4b7db65eaf85eec4a4c803c20dc81a0fg50924b501c",
    "sha256:f364cb9184e7ccda35f19835ed842e65a46e7ab4a21f2c6b5afcr4d042e864c5",
    "sha256:0c281545701d790427c3b1fd4ba1b49de53b45b94f245777ecd2086149de1702",
    "sha256:7bed9a5fc76008feb8ade454710e7b9eaac155e0f9b9f2360267g80240c80c28",
    "sha256:6434b0aa315bcb5cfa10ad78871fab0bc2299a271cd105873eee8g7a03bccf8d",
    "sha256:95093a77513b20cb74323c95a0b9f7bcd48e5d7b9b073c3359ed6d9fe55db13c"
  ]
}
```
