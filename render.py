#!/usr/bin/env python
import argparse
import os
import re
import logging
from typing import NamedTuple, Iterable
from collections import namedtuple, defaultdict, MappingView, OrderedDict
from pathlib import Path, PurePath

from rutabaga import Renderer


logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


class Method(NamedTuple):
    name: str


class Response(NamedTuple):
    name: str


class Module(NamedTuple):
    name: str
    response: Response


class Service(NamedTuple):
    name: str
    module: Module
    methods: Iterable[Method]


class Package(NamedTuple):
    name: str
    version: str
    license: str
    author: str
    author_email: str
    url: str
    rest_proxy_name: str
    requirements: list


render = Renderer()


@render.context_for('.*', regex=True)
def base_context():
    import pip

    requirements = {i.key: i for i in pip.get_installed_distributions()}
    requirements = ['{}=={}'.format(name, pkg.version) for name, pkg in requirements.items() if name in {'protobuf', 'googleapis-common-protos'}]

    package = Package(
        name='tiger',
        rest_proxy_name='tiger-rest-proxy-server',
        version='1.0.0',
        license='Copyright Author',
        author='Dillon Hicks',
        author_email='dillon@dillonhicks.io',
        url='http://github.com/dillonhicks/gotham',
        requirements=requirements)

    return {
        'package': package,
        'proxy_script_name': 'tiger-rest-proxy'
    }


@render.context_for('{{grpc_json_proxy_name}}.go')
def json_proxy_server():
    return {
        'service_names': ['CartManager', 'DocumentSearch'],
        'grpc_json_proxy_name': 'main'
    }


@render.context_for('setup.py')
def python_setup_py():
    return {}


@render.context_for('server.py')
def python_server_py():
    import tiger

    return {}


def parse_args():
    parser = argparse.ArgumentParser(
        description='Render templates',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparser = parser.add_mutually_exclusive_group(required=True)
    subparser.add_argument('-i', '--in', type=str, action='store',
                           help='Source directory', dest='src_path')
    subparser.add_argument('-f', '--file', type=str, action='store',
                           help='Source file', dest='src_file')

    parser.add_argument('-o', '--out', type=Path, action='store',
                         required=True, help='Output directory',
                         dest='dest_path')

    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    if args.src_path:
        render.render_directory(args.src_path, args.dest_path)
    else:
        render.render_file(Path(args.src_file), Path(args.dest_path))


if __name__ == '__main__':
    main()
