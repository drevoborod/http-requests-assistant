import json
import re
from itertools import zip_longest

import requests
import yaml
from structure import Request, Structure, URL_PARTS_TEMPLATE


STRUCTURE_FILE = "structure.yml"


class StructureParser:
    def __init__(self):
        self.structure_file_name = STRUCTURE_FILE
        self.parsed = self._parse()
        self.structure = self._prepare()

    def _parse(self):
        with open(self.structure_file_name, 'r') as file:
            return yaml.safe_load(file)

    def _prepare(self):
        http_requests = {}
        for key, value in self.parsed["http_requests"].items():
            data = dict(
                name=value["name"],
                url=value["url"],
                method=value["method"]
            )
            if headers := value.get("headers"):
                data["headers"] = headers
            if body := value.get("body"):
                data["body"] = body
            if query_params := value.get("query_params"):
                data["query_params"] = query_params
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
        return requests.request(
            method=request_object.method,
            url=url,
            params=query_params,
            headers=headers,
            json=body
        )
    except requests.exceptions.RequestException as err:
        return err
