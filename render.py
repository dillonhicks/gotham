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



class Request(NamedTuple):
    name: str

class Response(NamedTuple):
    name: str

class Method(NamedTuple):
    name: str
    response: Response
    request: Request

class Module(NamedTuple):
    name: str


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
    requirements: list


class Server(NamedTuple):
    default_port: int
    rest_proxy_script: str


render = Renderer()


@render.context_for('.*', regex=True)
def base_context():
    import pip

    requirements = {i.key: i for i in pip.get_installed_distributions()}
    requirements = ['{}=={}'.format(name, pkg.version) for name, pkg in requirements.items() if name in {'protobuf', 'googleapis-common-protos'}]

    package = Package(
        name='tiger',
        version='1.0.0',
        license='Copyright Author',
        author='Dillon Hicks',
        author_email='dillon@dillonhicks.io',
        url='http://github.com/dillonhicks/gotham',
        requirements=requirements)

    server = Server(
        default_port=8081,
        rest_proxy_script='{}-rest-proxy'.format(package.name))

    return {
        'package': package,
        'server': server,
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


from itertools import chain
from google.protobuf import service

def get_methods(svc):
    for m in svc.DESCRIPTOR.methods:
        yield Method(
            name=m.name,
            request=Request(svc.GetRequestClass(m).DESCRIPTOR.name),
            response=Request(svc.GetResponseClass(m).DESCRIPTOR.name))


def get_module(mod):
    return Module(name=mod.__name__.rsplit('.', 1)[-1])


def get_services(mod):
    for name in dir(mod):
        value = getattr(mod, name)
        try:
            if issubclass(value, service.Service) and not name.endswith('Stub'):
                yield Service(
                    name=value.DESCRIPTOR.name,
                    module=get_module(mod),
                    methods=list(get_methods(value)))
        except: continue

@render.context_for('server-stubs.py')
def python_server_py():
    tiger_dir = Path.cwd() / 'build' / 'python' / 'tiger'
    import sys
    sys.path.append(str(tiger_dir))
    import tiger
    from tiger import cart_pb2, search_pb2
    mods = cart_pb2, search_pb2
    from pprint import pprint
    services = list(chain.from_iterable(get_services(mod) for mod in mods))
    pprint(services)
    return dict(services=services)


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
