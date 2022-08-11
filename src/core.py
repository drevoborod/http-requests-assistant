from dataclasses import dataclass, field
import re

import yaml


STRUCTURE_FILE = "structure.yml"


@dataclass
class RequestParam:
    choices: list = field(default_factory=list)
    text: str = None
    description: str = ""


@dataclass
class Request:
    name: str
    url: str
    type: str
    headers: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)
    params: dict[str, RequestParam] = field(init=False)

    def __post_init__(self):
        self.params = {}
        url_keys = re.findall(r"\{.*}", self.url)
        for item in url_keys:
            kv = item.strip("{}")
            self.params[kv] = RequestParam(text=kv)
        for key, value in self.body.items():
            params = {}
            if text := value.get("default"):
                params["text"] = str(text)
            if description := value.get("description"):
                params["description"] = description
            if choices := value.get("choices"):
                params["choices"] = choices
            self.params[key] = RequestParam(**params)


@dataclass
class Structure:
    http_requests: dict[str, Request]


class Parser:
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
