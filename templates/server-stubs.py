"""Python Stub implementation of {{package.name}}"""
from concurrent import futures
import time

import grpc

{% for service in services %}
from {{package.name}} import {{service.module.name}}
{% endfor %}

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

{% for service in service %}}
class {{service.name}}}({{package_name}}.{{service.name}}Servicer):

{% for method in service.methods %}
    def {{method.name}}(self, request, context):
        return {{package.name}}.{{method.response.name}}()
{% endfor %}
{% endfor %}


def serve():

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
{% for service in services %}
    {{service.module.name}}.add_{{service.name}}Servicer_to_server({{service.name}}(), server)
{% endfor %}
    server.add_insecure_port('[::]:{{default_port}}')
    server.start()

    proxy_process = None

    try:
        if with_proxy_server:
            proxy_process = Popen(['{{rest-proxy-server-exe}}'])
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        if proxy_process is not None:
            proxy_process.terminate()

        server.stop(0)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Run {{project.name}}, optionally with the REST Proxy Server',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-p', '--port', type=str, action='store',
                        required=True, help='Source directory',
                        dest='src_path')

    parser.add_argument('--with-proxy-server', action='store_true',
                        default=False, help='Start the rest proxy server')

    args = parser.parse_args()
    return args


    serve()


if __name__ == '__main__':
    main()
