"""Python Client implementation of {{package.name}}"""
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import abc
import concurrent.futures
import logging
import threading
import time
from abc import abstractmethod
from collections import namedtuple
from functools import partial

import grpc
import requests
import six
from google.api.annotations_pb2 import http as google_api_http
from google.protobuf.json_format import Parse, MessageToJson
from google.protobuf.message import Message
from thundersnow import urlutil
from thundersnow.precondition import check_argument, check_state, IllegalArgumentError, IllegalStateError
from thundersnow.predicate import is_not_none
from thundersnow.reflection import class_name, name_of
from thundersnow.type import sentinel


__all__ = (
    'ClientError',
    'ConfigurationError',
    'HTTPClient',
    'InvalidRequestError',
)


LOG = logging.getLogger(__name__)

_missing = sentinel('MISSING_DESCRIPTOR')
protobuf_to_json = MessageToJson


{% for service in services %}
from {{package.name}} import {{service.module.name}}, {{service.module.name}}_grpc
{% endfor %}


{% for service in services %}
class {{service.name}}Client({{service.module.name}}_grpc.{{service.name}}Stub):
    def __init__(self, host, port, secure=False):
        if secure:
            raise NotImplementedError()
        else:
            channel = grpc.insecure_channel('{}:{}'.format(host, port))

        super({{service.name}}Client, self).__init__(channel)

{% for method in service.methods %}
    @property
    def {{method.python_friendly_name}}(self):
        return self.{{method.name}}
{% endfor %}
{% endfor %}

def protobuf_name(obj):
    descriptor = getattr(obj, 'DESCRIPTOR', _missing)
    name = getattr(descriptor, 'name', _missing)
    if name is _missing:
        return name_of(obj)
    return name


class ClientError(Exception):
    pass


class InvalidRequestError(ClientError, IllegalArgumentError):
    pass


class ConfigurationError(ClientError, IllegalStateError):
    pass


class _ResponseWrapper(namedtuple(
        'Response', (
            'response',
            'meta',
        ))):

    MAX_RESPONSE_DISPLAY_LEN = 256

    @staticmethod
    def wrap(response, meta):
        return _ResponseWrapper(response=response, meta=meta)


class AbstractClient(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def call(self, request):
        # type: (Message) -> _ResponseWrapper
        pass

    @abc.abstractmethod
    def call_async(self, request):
        # type: (Message) -> _ResponseWrapper
        pass


class BaseReflectionClient(AbstractClient):

    def __init__(self, ProtoAPI, base_url, workers=4):
        super(BaseReflectionClient, self).__init__()

        self.base_url = base_url
        self.Service = ProtoAPI
        self.descriptor = ProtoAPI.GetDescriptor()
        self.headers = {'Content-Type': 'application/json'}
        self.executor = concurrent.futures.ThreadPoolExecutor(workers)
        self.cookies = None
        self.lock = threading.Lock()

    def call(self, request):
        LOG.info('%s begin call for %s', class_name(self), protobuf_name(request))
        # This is based on convention
        # MyOperationRequest -> MyOperation -> MyOperationResponse
        operation = protobuf_name(request).replace('Request', '')
        method_desc = self.descriptor.FindMethodByName(operation)

        check_argument(
            is_not_none(method_desc),
            '{} does not define any operation that accepts {}',
            protobuf_name(self.Service), protobuf_name(request),
            Error=InvalidRequestError)

        try:
            http_rule = method_desc.GetOptions().Extensions[google_api_http]
        except KeyError:
            http_rule = None
            verb = None

        check_state(
            is_not_none(http_rule),
            'Operation {!r} does not define option (google.api.http)', operation,
            Error=ConfigurationError)

        verb = http_rule.WhichOneof('pattern')
        route = getattr(http_rule, verb, None)

        # The base url should define a trainling slash
        url = urlutil.join(self.base_url, route)

        LOG.info('calling %s (%s %s)', protobuf_name(self.Service), verb, url)
        response = self._do_call(url, verb, request)

        LOG.info(
            'http_status: %s', response.status_code)

        ResponseClass = self.Service.GetResponseClass(method_desc)
        LOG.info('Unpacking response into %s', protobuf_name(ResponseClass))

        rpc_response = Parse(response.content, ResponseClass(), ignore_unknown_fields=True)
        return _ResponseWrapper.wrap(rpc_response, response)

    def call_async(self, request):
        return self.executor.submit(partial(self.call, request))

    @abstractmethod
    def _do_call(self, url, verb, request):
        pass

    def __str__(self):
        return '{}(service={!r}, base_url={!r})'.format(
            class_name(self), protobuf_name(self.Service), self.base_url)

    def __repr__(self):
        return ''.join(['<', str(self), '>'])


class HTTPClient(BaseReflectionClient):
    MAX_RETRIES = 3

    def __init__(self, ProtoAPI, base_url, workers=4):
        super(HTTPClient, self).__init__(ProtoAPI, base_url, workers=workers)
        self.session = requests.Session()
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def _retriable_call(self, url, verb, data):

        session_method = getattr(self.session, verb)

        for retry_number in range(1, self.MAX_RETRIES + 1):
            try:
                return session_method(url, data=data, headers=self.headers)
            except requests.exceptions.ConnectionError:
                if retry_number == self.MAX_RETRIES:
                    raise
                time.sleep(0.1 * retry_number)

    def _do_call(self, url, verb, request):
        data = protobuf_to_json(request)

        response = self._retriable_call(url, verb, data)

        LOG.info('Response: %s Cookies %s', response, response.cookies)

        if self.cookies is None:
            with self.lock:
                if self.cookies is None:
                    self.cookies = response.cookies

        return response


{% for service in services %}
class {{service.name}}RestClient(HTTPClient):
    def __init__(self, host, port):
        super({{service.name}}RestClient, self).__init__({{service.module.name}}.{{service.name}},'{}:{}'.format(host, port))

{% endfor %}
