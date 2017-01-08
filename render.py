#!/usr/bin/env python
import argparse
import importlib
import inspect
import logging
import pkgutil
import sys
from itertools import chain
from pathlib import Path
from typing import NamedTuple, Iterable

import pip
from thundersnow import ioutil
from boltons.strutils import camel2under
from google.api.annotations_pb2 import http as google_api_http
from google.protobuf import service
from rutabaga import Renderer
import yaml


logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)


class Configuration(NamedTuple):
    name: str
    version: str
    configfile: Path
    output_dir: Path
    author: str
    author_email: str
    project_url: str
    default_port: int


class config:
    pass


class Request(NamedTuple):
    name: str


class Response(NamedTuple):
    name: str


class Method(NamedTuple):
    name: str
    response: Response
    request: Request
    python_friendly_name: str
    route: str
    verb: str
    rest_name: str


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
    # TODO: Slice out requirments needed for pkg
    requirements = [i.key for i in pip.get_installed_distributions()]
    # requirements = ['{}=={}'.format(name, pkg.version) for name, pkg in requirements.items() ]

    package = Package(
        name=config.name,
        version=config.version,
        license='Copyright',
        author=config.author,
        author_email=config.author_email,
        url=config.project_url,
        requirements=requirements)

    server = Server(
        default_port=config.default_port,
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


def get_methods(svc):

    for m in svc.DESCRIPTOR.methods:
        http_rule = m.GetOptions().Extensions[google_api_http]
        verb = http_rule.WhichOneof('pattern')
        route = getattr(http_rule, verb)

        yield Method(
            name=m.name,
            python_friendly_name=camel2under(m.name),
            route=route,
            verb=verb,
            rest_name='{}_{}'.format(verb, camel2under(m.name)),
            request=Request(svc.GetRequestClass(m).DESCRIPTOR.name),
            response=Request(svc.GetResponseClass(m).DESCRIPTOR.name))


def get_module(mod):
    return Module(name=mod.__name__.rsplit('.', 1)[-1])


def get_services(mod):
    for name in dir(mod):
        value = getattr(mod, name)

        try:
            if inspect.isclass(value) and issubclass(value, service.Service) and not name.endswith('Stub'):
                yield Service(
                    name=value.DESCRIPTOR.name,
                    module=get_module(mod),
                    methods=list(get_methods(value)))
        except:
            LOG.exception('Something Dumb Happened')
            continue


@render.context_for('server-stubs.py')
def python_server_py():
    sys.path.append(str(config.output_dir))
    LOG.info('PythonPath: %s', sys.path)

    package = importlib.import_module(config.name)
    results = pkgutil.iter_modules(package.__path__, package.__name__ + '.')
    modules = [importlib.import_module(r.name) for r in results if r.name.endswith('pb2')]
    services = list(chain.from_iterable(get_services(mod) for mod in modules))
    LOG.info('Found service defs: %s', services)

    return dict(services=services)


@render.context_for('client.py')
def python_client_py():
    return python_server_py()


def parse_config(configfile):
    data = yaml.load(ioutil.fulltext(configfile))
    data['configfile'] = configfile
    data['output_dir'] = Path.cwd() / 'build' / 'python'
    for key, value in Configuration(**data)._asdict().items():
        setattr(config, key, value)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Render templates',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-c', '--config', type=Path, action='store',
                           help='Configuration for pkg name and build dir',
                           dest='config', required=True)

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
    logging.basicConfig(level=logging.INFO)

    parse_config(args.config)

    if args.src_path:
        render.render_directory(args.src_path, args.dest_path)
    else:
        render.render_file(Path(args.src_file), Path(args.dest_path))


if __name__ == '__main__':
    main()
