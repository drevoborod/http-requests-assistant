import json
import logging
import re
from itertools import zip_longest

import requests
from requests.exceptions import JSONDecodeError, RequestException
import yaml

from .structure import (General, Request, RequestSection, Structure, TEMPLATE_TO_SPLIT_URL, TEMPLATE_TO_REPLACE_PARAM,
                        RequestParamsNames, RequestSectionParamsNames, RootParamsNames, TypeNames, HTTP_LOG)


STRUCTURE_FILE = "structure.yml"


class StructureParser:
    _parsed = None
    _structure = None

    def __init__(self, structure_file_name=STRUCTURE_FILE):
        self.structure_file_name = structure_file_name

    @property
    def structure(self):
        if not self._parsed:
            self._parsed = self._parse_file()
        if not self._structure:
            self._structure = self._prepare()
        return self._structure

    def _parse_file(self) -> dict:
        with open(self.structure_file_name, 'r') as file:
            return yaml.safe_load(file)

    def _prepare(self):
        http_requests = {}
        for key, value in self._parsed[RootParamsNames.http_requests].items():
            data = dict(
                name=value[RequestParamsNames.name.name],
                url=value[RequestParamsNames.url.name],
                method=value[RequestParamsNames.method.name]
            )

            for section_name in (
                RequestParamsNames.headers,
                RequestParamsNames.query_params,
                RequestParamsNames.body
            ):
                if section := value.get(section_name):
                    section_dict = {RequestSectionParamsNames.json.name: section[RequestSectionParamsNames.json.name]}
                    if keys := section.get(RequestSectionParamsNames.keys.name):
                        section_dict[RequestSectionParamsNames.keys.name] = keys
                    data[section_name.name] = RequestSection(**section_dict)
            http_requests[key] = Request(**data)
        if self._parsed.get(RootParamsNames.general.name):
            return Structure(
                http_requests=http_requests,
                general=General(**self._parsed[RootParamsNames.general.name])
            )
        return Structure(http_requests)


def send_request(request_object: Request, enable_log=False, log_file=HTTP_LOG):
    if enable_log:
        logger = logging.Logger('requests sender')
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                               datefmt='%Y-%m-%d %H:%M:%S.%s'))
        logger.addHandler(handler)
        logger.info(request_object)
    raw_body = _prepare_body(request_object.body)
    query_params = _prepare_section(request_object.query_params)
    headers = _prepare_section(request_object.headers)
    url_parts = [value.current_value for value in request_object.parsed_url_parts]
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
        logger.info(f'######## Request: {request_object.name} #######\n'
                    f'url: {prepared_request.url}\n'
                    f'Headers: {prepared_request.headers}\n'
                    f'Body: {prepared_request.body}\n')
    session = requests.session()
    try:
        response = session.send(prepared_request)
    except RequestException as err:
        if enable_log:
            logger.error(err)
        return str(err)
    else:
        try:
            resp = json.dumps(response.json(), indent=4, ensure_ascii=False)
            if enable_log:
                logger.info(resp)
            return resp
        except (JSONDecodeError, UnicodeDecodeError):
            resp = response.content.decode(encoding="utf-8")
            if enable_log:
                logger.info(resp)
            return resp


def _prepare_body(body: RequestSection) -> bytes:
    if body.json:           # prevent sending empty json in request body
        return _fill_template(body).encode('utf-8')


def _prepare_section(section: RequestSection) -> dict:
    if section.parsed_keys:
        return json.loads(_fill_template(section))
    return section.json


def _fill_template(section: RequestSection):
    json_template = json.dumps(section.json)
    for key, value in section.parsed_keys.items():
        placeholder = TEMPLATE_TO_REPLACE_PARAM % key
        if placeholder not in json_template:
            raise KeyError(f'Key "{key}" is defined but never used')
        json_template = json_template.replace(placeholder, _prepare_type_to_replace(value.current_value, value.type))
    return json_template


def _prepare_type_to_replace(data: str, param_type: str) -> str:
    match param_type:
        case TypeNames.empty.value:
            if data.isdecimal() or data in ("null", "true", "false"):
                return data
            return f'"{data}"'          # need to return quotes
        case TypeNames.string.value:
            return f'"{data}"'          # need to return quotes
        case TypeNames.number.value | TypeNames.boolean.value:
            return data
        case TypeNames.null.value:
            return "null"
