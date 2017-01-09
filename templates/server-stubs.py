"""Python Stub implementation of {{package.name}}"""
from concurrent import futures
import pkg_resources
import time
from subprocess import Popen, PIPE

import grpc
from thundersnow.dateutil import Delta

{% for service in services %}
from {{package.name}} import {{service.module.name}}, {{service.module.name}}_grpc
from {{package.name}}.{{service.module.name}} import ({% for method in service.methods %}
    {{method.request.name}},
    {{method.response.name}},
{% endfor %})
{% endfor %}


{% for service in services %}
class {{service.name}}({{service.module.name}}_grpc.{{service.name}}Servicer):
{% for method in service.methods %}
    def {{method.name}}(self, request, context):
        # type: ({{method.request.name}}, grpc.RpcContext) -> {{method.response.name}}

        return {{method.response.name}}()
{% endfor %}
{% endfor %}

def serve(port, with_proxy_server=False):

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
{% for service in services %}
    {{service.module.name}}_grpc.add_{{service.name}}Servicer_to_server({{service.name}}(), server)
{% endfor %}
    server.add_insecure_port('[::]:{}'.format(port))
    server.start()

    proxy_process = None
    proxy_filepath = pkg_resources.resource_filename('{{package.name}}', 'bin/rest-proxy-server.bin')
    if sys.platform.lower() == 'darwin':
        proxy_filepath = '.'.join([proxy_filepath, 'darwin'])

    try:
        if with_proxy_server:
            proxy_process = Popen([proxy_filepath])
        while True:
            time.sleep(Delta.one_day.total_seconds())
    except KeyboardInterrupt:
        if proxy_process is not None:
            proxy_process.terminate()

        server.stop(0)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Run {{package.name}}, optionally with the REST Proxy Server',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-p', '--port', type=str, action='store',
                        default={{server.default_port}},
                        help='server port')

    parser.add_argument('--with-proxy-server', action='store_true',
                        default=False, help='Start the rest proxy server')

    args = parser.parse_args()
    serve(args.port, args.with_proxy_server)


if __name__ == '__main__':
    main()
