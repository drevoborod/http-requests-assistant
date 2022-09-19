

import requests
import yaml
from structure import Request, Structure


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
            params = dict(
                name=value["name"],
                url=value["url"],
                type=value["type"]
            )
            if headers := value.get("headers"):
                params["headers"] = headers
            if body := value.get("body"):
                params["body"] = body
            http_requests[key] = Request(**params)
        return Structure(http_requests)


def request(request_object: Request):
    response = requests.request(
        method=request_object.method,
        url=request_object.url,
        headers=request_object.headers,
        json=request_object.body
    )
    # if response.status_code not in (requests.codes.ok, requests.codes.created):
    #     pass
    return response.content
