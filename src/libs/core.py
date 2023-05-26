import json
from logging import Logger, FileHandler
import re
from itertools import zip_longest

import requests
from requests.exceptions import JSONDecodeError, RequestException
import yaml

from .structure import (General, Request, RequestSection, Structure, TEMPLATE_TO_SPLIT_URL, TEMPLATE_TO_REPLACE_PARAM,
                        RequestParamsNames, RequestSectionParamsNames, RootParamsNames, TypeNames, MISSING)


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
        logger.info(f'\n######## Request: {request_object.name} #######\n'
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
