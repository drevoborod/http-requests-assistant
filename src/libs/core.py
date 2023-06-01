from copy import deepcopy
import json
import logging
import re
from itertools import zip_longest

import requests
from requests.exceptions import JSONDecodeError, RequestException
import yaml

from .structure import (General, Request, RequestSection, Structure, TEMPLATE_TO_SPLIT_URL, TEMPLATE_TO_REPLACE_PARAM,
                        RequestParamsNames, RequestSectionParamsNames, RootParamsNames, TypeNames, JsonValuesMatch,
                        HTTP_LOG)


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
    body_json = _prepare_section(request_object.body)
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
            json=body_json)
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
            text_response = json.dumps(response.json(), indent=4, ensure_ascii=False)
            if enable_log:
                logger.info(text_response)
            return text_response
        except (JSONDecodeError, UnicodeDecodeError):
            text_response = response.content.decode(encoding="utf-8")
            if enable_log:
                logger.info(text_response)
            return text_response


def _prepare_section(section: RequestSection):
    result = deepcopy(section.json)
    for key, request_param in section.parsed_keys.items():
        placeholder = TEMPLATE_TO_REPLACE_PARAM % key
        result = _replace_template(result, placeholder, request_param.current_value, request_param.type)
    return result


def _replace_template(data: [dict, list], template: str, new_value: str, value_type: str):
    if isinstance(data, dict):
        for key, value in data.items():
            if value == template:
                data[key] = _prepare_type_to_replace(new_value, value_type)
            elif isinstance(value, (dict, list)):
                data[key] = _replace_template(value, template, new_value, value_type)
    elif isinstance(data, list):
        for number, item in enumerate(data):
            if item == template:
                data[number] = _prepare_type_to_replace(new_value, value_type)
            elif isinstance(item, (dict, list)):
                data[number] = _replace_template(item, template, new_value, value_type)
    return data


def _prepare_type_to_replace(data, param_type: str):
    match param_type:
        case TypeNames.empty.value:
            if data.isdecimal():
                return int(data)

            try:
                return JsonValuesMatch[data.casefold()].value
            except KeyError:
                return data
        case TypeNames.string.value:
            return data
        case TypeNames.number.value:
            return int(data)
        case TypeNames.boolean.value:
            try:
                return JsonValuesMatch[data.casefold()].value
            except KeyError:
                raise ValueError(f"Incorrect value for boolean type: {data}")
