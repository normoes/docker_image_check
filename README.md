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
* `--debug` shows debug logs.

## Configuration

Images are read from `./images.txt` by default. The option `--image-file` can be used to read images from a configuration file other than the default one.

Images in `./images.txt` can be added by:
* full name
* regular expression


Comments in `./images.txt` start with `#`.

Blank lines are ignored.

## Examples

Coming back to the `whitelsit` scenario above:
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
* **Hint**:
    ```
      # Using 'blacklist' mode swaps the results.
      INFO:__main__:[blacklist] Good image found: 'malicious_repo/some_image'.
      INFO:__main__:[blacklist] Good image found: 'python:3.7-alpine3.10'.
      INFO:__main__:[blacklist] Good image found: 'developer_a/log_converter'.
      INFO:__main__:[blacklist] Bad image found: 'my_company/nginx'.
      INFO:__main__:[blacklist] Bad image found: 'my_company/service'.
      my_company/nginx
      my_company/service
    ```

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
* **Hint**:
    ```
      # Using 'whitelist' mode swaps the results.
      INFO:__main__:[whitelist] Good image found: 'malicious_repo/some_image'.
      INFO:__main__:[whitelist] Bad image found: 'python:3.7-alpine3.10'.
      python:3.7-alpine3.10`
    ```
