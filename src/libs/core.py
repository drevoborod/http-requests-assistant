import json
import re
from itertools import zip_longest

import requests
import yaml

from .structure import (Request, RequestBody, Structure, URL_PARTS_TEMPLATE,
                        RequestParamsNames, BodyParamsNames, RootParamsNames)


STRUCTURE_FILE = "structure.yml"


class StructureParser:
    def __init__(self, structure_file_name=STRUCTURE_FILE):
        self.structure_file_name = structure_file_name
        self.parsed = None
        self._structure = None

    @property
    def structure(self):
        if not self.parsed:
            self.parsed = self._parse()
        if not self._structure:
            self._structure = self._prepare()
        return self._structure

    def _parse(self) -> dict:
        with open(self.structure_file_name, 'r') as file:
            return yaml.safe_load(file)

    def _prepare(self):
        http_requests = {}
        for key, value in self.parsed[RootParamsNames.http_requests].items():
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
        return Structure(http_requests)


def send_request(request_object: Request):
    ###
    # print(request_object)
    ###
    url_parts = [value.current_value for value in request_object.parsed_url_parts]
    body = {name: value.current_value for name, value in request_object.parsed_body.items()}
    query_params = {name: value.current_value for name, value in request_object.parsed_query_params.items()}
    headers = {name: value.current_value for name, value in request_object.parsed_headers.items()}
    splitted_url = re.split(URL_PARTS_TEMPLATE, request_object.url)
    url = "".join([item for sublist in zip_longest(splitted_url, url_parts, fillvalue="") for item in sublist])
    for key, value in body.items():
        try:
            replace = json.loads(value)
        except Exception:
            pass
        else:
            body[key] = replace
    ###
    # for x in (url, body, url_parts, headers, query_params):
    #     print(x)
    ###
    try:
        response = requests.request(
            method=request_object.method,
            url=url,
            params=query_params,
            headers=headers,
            json=body
        )
    except requests.exceptions.RequestException as err:
        return str(err)
    else:
        try:
            return json.dumps(response.json(), indent=4, ensure_ascii=False)
        except Exception:
            return response.content.decode(encoding="utf-8")
