"""Python Stub implementation of tiger"""
from concurrent import futures
import time

from subprocess import Popen, PIPE
import grpc


from tiger import cart_pb2, cart_pb2_grpc

from tiger import search_pb2, search_pb2_grpc


_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class CartManager(cart_pb2_grpc.CartManagerServicer):


    def GetCart(self, request, context):
        return cart_pb2.GetCartResponse()


class DocumentSearch(search_pb2_grpc.DocumentSearchServicer):


    def FindDocument(self, request, context):
        return search_pb2.FindDocumentResponse()




def serve(port, with_proxy_server=False):

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    cart_pb2_grpc.add_CartManagerServicer_to_server(CartManager(), server)

    search_pb2_grpc.add_DocumentSearchServicer_to_server(DocumentSearch(), server)

    server.add_insecure_port('[::]:{}'.format(port))
    server.start()

    proxy_process = None

    try:
        if with_proxy_server:
            proxy_process = Popen(['tiger-rest-proxy'])
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        if proxy_process is not None:
            proxy_process.terminate()

        server.stop(0)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Run tiger, optionally with the REST Proxy Server',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-p', '--port', type=str, action='store',
                        default=8081,
                        help='server port')

    parser.add_argument('--with-proxy-server', action='store_true',
                        default=False, help='Start the rest proxy server')

    args = parser.parse_args()
    serve(args.port, args.with_proxy_server)


if __name__ == '__main__':
    main()