"""
This tool can be used to report unwanted docker images in production environemnts.

By default it returns unwanted images that should not be used by running containers.

Two modes are supported:
* **'blacklist'**: Images defined in 'images.txt' are considered **bad**.
  - **Returns images found in 'images.txt'.**
* **'whitelist'**: Images defined in 'images.txt' are considered **good**.
  - **Returns images not found in 'images.txt'.**

Additional flags:
* '--debug' shows debug logs.

Comments in the files start with '#'.

**Example**:
* Running 'blacklist' mode.
* **Use case**: Some docker repositories/images have been flagegd as malicious, some versions should not be used anymore, etc..
* Assume you are running a container based on 'malicious_repo/some_image'.
* This is your 'images.txt':
  # comment
  # blank lines are ignored
  malicious_repo/*
  some_repo/malicious_image
  python:2.7*
* `python app.py blacklist`.
* **Output**:
      + INFO:__main__:[blacklist] Bad image found: 'malicious_repo/some_image'.
      + INFO:__main__:[blacklist] Good image found: 'python:3.7-alpine3.10'.
      + malicious_repo/some_image
* **Hint**:
    - Using 'whitelist' mode swaps the results.
    - In this example the log message ('Good', 'Bad') does not matter.
    - INFO:__main__:[whitelist] Good image found: 'malicious_repo/some_image'.
    - INFO:__main__:[whitelist] Bad image found: 'python:3.7-alpine3.10'.
    - python:3.7-alpine3.10

"""

import docker
import logging
import sys
import argparse
import re

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_images_from_file(image_file=""):
    images = set()
    if image_file:
        with open(image_file, "r") as file_handler:
            for image in file_handler.readlines():
                image_ = image.strip()
                if image_ and not image_.startswith('#'):
                    images.add(image_)
    logger.debug(f"Images in '{image_file}': '{images}'.")

    return images
    

def detailed_containers(mode=None, images=set(), client=None):
    if not client:
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    images_found = set()
    containers = client.containers.list()
    image_names = set()

    for container in containers:
        image_names.add(container.attrs['Config']['Image'])
        # print(container.attrs)
        # print(container.stats(stream=False))

    logger.debug(f"Images used by running containers: '{image_names}'.")


    for image_name in image_names:
        is_match = False
        for image in images:
            p = re.compile(image)
            
            if image_name in images_found:
                image_ignored = True
                break
            is_match = not p.match(image_name) is None
            logger.debug(f"[{is_match}] for '{image_name}' and '{image}'.")
            if mode == "blacklist":
                if is_match:
                    images_found.add(image_name)
                    logger.info(f"[{mode}] Bad image found: '{image_name}'.") 
                    break
            elif mode == "whitelist":
                if is_match:
                    logger.info(f"[{mode}] Good image found: '{image_name}'.") 
                    break
        if mode == "blacklist" and not is_match:
            logger.info(f"[{mode}] Good image found: '{image_name}'.") 
        if mode == "whitelist" and not is_match:
            logger.info(f"[{mode}] Bad image found: '{image_name}'.") 
            images_found.add(image_name)

    return sorted(list(images_found))


def main():
    try:
        from _version import __version__
    except:
        __version__ = "develop"

    parser = argparse.ArgumentParser(
        description="Check docker images.",
        epilog="Example:\npython get_docker_container_info.py blacklist",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )


    # Same for all subcommnds
    config = argparse.ArgumentParser(add_help=False)

    config.add_argument(
        "--image-file", default="images.txt", help="Path to images.txt."
    )
    config.add_argument(
        "--debug", action="store_true", help="Show debug info."
    )

    subparsers = parser.add_subparsers(
        help="sub-command help", dest="subcommand"
    )
    subparsers.required = True

    blacklist = subparsers.add_parser(
        "blacklist",
        parents=[config],
        help="Images defined in 'images.txt' are considered **Bad**.",
    )
    whitelist = subparsers.add_parser(
        "whitelist",
        parents=[config],
        help="Images defined in 'images.txt' are considered **Good**.",
    )

    args = parser.parse_args()

    mode = args.subcommand
    debug = args.debug

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


    logger.info(f"Working in '{mode}' mode.")

    images = get_images_from_file(args.image_file)

    images_found = detailed_containers(mode=mode, images=images)
    for image in images_found:
        print(image)

    return 0


if __name__ == "__main__":
    sys.exit(main())
