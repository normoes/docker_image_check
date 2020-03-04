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
"""

import docker
import logging
import sys
import argparse
import re
from typing import Set, List, Dict
from dataclasses import dataclass
import json

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class Modes:
    """Modes to run the app with.
    """
    blacklist: str = "blacklist"
    whitelist: str = "whitelist"


def get_images_from_file(image_file:str="") -> Set:
    """Get docker images from file.

    Images can be defined as complete name string or as regular expression.
    """
    images = set()
    if image_file:
        with open(image_file, "r") as file_handler:
            for image in file_handler.readlines():
                image_ = image.strip()
                if image_ and not image_.startswith('#'):
                    images.add(image_)
    logger.debug(f"Images in '{image_file}': '{images}'.")

    return images
    

def get_running_containers(client=None) -> List:
    """Get docker images from running docker containers.
    """
    if not client:
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    # https://docker-py.readthedocs.io/en/stable/containers.html
    # sparse (bool) – Do not inspect containers.
    #                 Returns partial information, but guaranteed not to
    #                 block. Use Container.reload() on resulting objects
    #                 to retrieve all attributes.
    containers = client.containers.list(sparse=True)
    container_images = set()
    for container in containers:
        try:
            container_images.add(container.attrs["Image"])
        except KeyError as e:
            logger.info(f"No detailed information about container '{container}'.")
        # print(container.stats(stream=False))

    logger.debug(f"Images used by running containers: '{container_images}'.")

    return container_images


def get_image_layers(images:Set=set(), client=None) -> Dict[str, List]:
    """Get the underlying docker image layers of the given docker images.
    """
    if not client:
        client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    layers = {}
    for image in images:
        try:
            layers[image] = client.images.get(name=image).attrs["RootFS"].get("Layers", [])
        except KeyError as e:
            logger.info(f"No detailed information about image '{image}'.")

    print(layers)
    return layers


def get_used_images(mode:Modes=Modes.whitelist, images_from_file:Set=set(), container_images:Set=set()) -> List:
    """Filter docker images according to mode.

    Depends on mode:
    * blacklist
    * whitelist
    """
    images_found = set()
    for image_name in container_images:
        is_match = False
        for image in images_from_file:
            p = re.compile(image)
            # Avoid checking the same image several times.           
            if image_name in images_found:
                break
            is_match = not p.match(image_name) is None
            logger.debug(f"[{is_match}] for '{image_name}' and '{image}'.")
            if mode == Modes.blacklist:
                if is_match:
                    # Add image to the blacklist.
                    images_found.add(image_name)
                    logger.info(f"[{mode}] Bad image found: '{image_name}'.") 
                    break
            elif mode == Modes.whitelist:
                if is_match:
                    logger.info(f"[{mode}] Good image found: '{image_name}'.") 
                    break
        if mode == Modes.blacklist and not is_match:
            logger.info(f"[{mode}] Good image found: '{image_name}'.") 
        if mode == Modes.whitelist and not is_match:
            # Add image to the whitelist.
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
        "--layers", action="store_true", help="Show underlying docker image layers."
    )
    config.add_argument(
        "--debug", action="store_true", help="Show debug info."
    )

    subparsers = parser.add_subparsers(
        help="sub-command help", dest="subcommand"
    )
    subparsers.required = True

    blacklist = subparsers.add_parser(
        Modes.blacklist,
        parents=[config],
        help="Images defined in 'images.txt' are considered **Bad**.",
    )
    whitelist = subparsers.add_parser(
        Modes.whitelist,
        parents=[config],
        help="Images defined in 'images.txt' are considered **Good**.",
    )

    args = parser.parse_args()

    mode = args.subcommand
    layers = args.layers
    debug = args.debug

    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


    logger.info(f"Working in '{mode}' mode.")

    # Get images from file.
    images_from_file = get_images_from_file(args.image_file)

    # Get docker images from running containers.
    container_images = get_running_containers()

    # Filter images according to mode.
    images_found = get_used_images(mode=mode, images_from_file=images_from_file, container_images=container_images)

    if layers:
        # Get underlying docker image layers.
        image_layers = get_image_layers(images=images_found)
        print(json.dumps(image_layers, indent=2))
    else:
        for image in images_found:
            print(image)

    return 0


if __name__ == "__main__":
    sys.exit(main())
