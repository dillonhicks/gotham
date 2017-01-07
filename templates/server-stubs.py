"""Python Stub implementation of {{package.name}}"""
from concurrent import futures
import time

from subprocess import Popen, PIPE
import grpc

{% for service in services %}
from {{package.name}} import {{service.module.name}}, {{service.module.name}}_grpc
{% endfor %}

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

{% for service in services %}
class {{service.name}}({{service.module.name}}_grpc.{{service.name}}Servicer):

{% for method in service.methods %}
    def {{method.name}}(self, request, context):
        return {{service.module.name}}.{{method.response.name}}()
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

    try:
        if with_proxy_server:
            proxy_process = Popen(['{{server.rest_proxy_script}}'])
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
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
