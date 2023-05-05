import json
from logging import Logger, FileHandler
import re
from itertools import zip_longest

import requests
import yaml

from .structure import (General, Request, RequestBody, Structure, TEMPLATE_TO_SPLIT_URL,
                        RequestParamsNames, BodyParamsNames, RootParamsNames)


STRUCTURE_FILE = "structure.yml"


class StructureParser:
    parsed = None
    _structure = None
    structure_file_name = STRUCTURE_FILE

    @classmethod
    @property
    def structure(cls):
        if not cls.parsed:
            cls.parsed = cls._parse()
        if not cls._structure:
            cls._structure = cls._prepare()
        return cls._structure

    @classmethod
    def _parse(cls) -> dict:
        with open(cls.structure_file_name, 'r') as file:
            return yaml.safe_load(file)

    @classmethod
    def _prepare(cls):
        http_requests = {}
        for key, value in cls.parsed[RootParamsNames.http_requests].items():
            data = dict(
                name=value[RequestParamsNames.name.name],
                url=value[RequestParamsNames.url.name],
                method=value[RequestParamsNames.method.name]
            )
            if headers := value.get(RequestParamsNames.headers):
                data[RequestParamsNames.headers.name] = headers
            if body := value.get(RequestParamsNames.body):
                data[RequestParamsNames.body.name] = RequestBody(
                    keys=body[BodyParamsNames.keys.name],
                    json=body[BodyParamsNames.json.name]
                )
            if query_params := value.get(RequestParamsNames.query_params):
                data[RequestParamsNames.query_params.name] = query_params
            http_requests[key] = Request(**data)
        if cls.parsed.get(RootParamsNames.general.name):
            return Structure(
                http_requests=http_requests,
                general=General(**cls.parsed[RootParamsNames.general.name])
            )
        return Structure(http_requests)


def send_request(request_object: Request):
    enable_log = True if StructureParser().structure.general.enable_http_log else False
    if enable_log:
        logger = Logger('requests sender')
        logger.addHandler(FileHandler(StructureParser().structure.general.http_log))
        logger.info(request_object)
    url_parts = [value.current_value for value in request_object.parsed_url_parts]
    raw_body = _prepare_body(request_object.body)
    query_params = {name: value.current_value for name, value in request_object.parsed_query_params.items()}
    headers = {name: value.current_value for name, value in request_object.parsed_headers.items()}
    splitted_url = re.split(TEMPLATE_TO_SPLIT_URL, request_object.url)
    url = "".join([item for sublist in zip_longest(splitted_url, url_parts, fillvalue="") for item in sublist])
    # For logging purposes:
    request = requests.Request(method=request_object.method,
            url=url,
            params=query_params,
            headers=headers,
            data=raw_body)
    prepared_request = request.prepare()
    if enable_log:
        logger.info(f'url: {prepared_request.url}\n'
                    f'Headers: {prepared_request.headers}\n'
                    f'Body: {prepared_request.body}\n')
    session = requests.session()
    try:
        response = session.send(prepared_request)
    except requests.exceptions.RequestException as err:
        if enable_log:
            logger.error(err)
        return str(err)
    else:
        try:
            resp = json.dumps(response.json(), indent=4, ensure_ascii=False)
            if enable_log:
                logger.info(resp)
            return resp
        except Exception:
            resp = response.content.decode(encoding="utf-8")
            if enable_log:
                logger.info(resp)
            return resp


def _prepare_body(body: RequestBody) -> bytes:
    if body.json:           # prevent sending empty json in request body
        json_template = json.dumps(body.json)
        for key, value in body.parsed_keys.items():
            json_template = json_template.replace('{{{%s}}}' % key, str(value.current_value).lower())
        return json_template.encode('utf-8')
