from dataclasses import dataclass, field
from enum import Enum
import re


URL_PARTS_TEMPLATE = r"\{(.*?)}"


class RootParamsNames(str, Enum):
    http_requests = "http_requests"
    general = "general"


class RequestParamsNames(str, Enum):
    name = "name"
    url = "url"
    method = "method"
    headers = "headers"
    query_params = "query_params"
    body = "body"


class NodeParamsNames(str, Enum):
    choices = "__choices__"
    description = "__description__"
    text = "__text__"


@dataclass
class RequestParam:
    choices: list = field(default_factory=list)
    text: str = None
    description: str = ""
    current_value: str = None   # should be set after a user commands to send request.


@dataclass
class Request:
    name: str
    url: str
    method: str
    headers: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)
    query_params: dict = field(default_factory=dict)
    # all adjustable parameters including URL parts in curl braces, query parameters, headers and body parameters:
    parsed_headers: dict[str, RequestParam] = field(init=False)
    parsed_body: dict[str, RequestParam] = field(init=False)
    parsed_query_params: dict[str, RequestParam] = field(init=False)
    parsed_url_parts: list[RequestParam] = field(init=False)

    def __post_init__(self):
        self.parsed_url_parts = []
        url_keys = re.findall(URL_PARTS_TEMPLATE, self.url)
        for item in url_keys:
            self.parsed_url_parts.append(RequestParam(text=item))
        self.parsed_body = self._prepare_params(self.body)
        self.parsed_query_params = self._prepare_params(self.query_params)
        self.parsed_headers = self._prepare_params(self.headers)

    @staticmethod
    def _prepare_params(params: dict):
        result = {}
        for key, value in params.items():
            data = {}
            if (text := value.get(NodeParamsNames.text)) is not None:  # support of boolean params in text area
                if isinstance(text, bool):
                    data[NodeParamsNames.choices.name] = [text, not text]
                else:
                    data[NodeParamsNames.text.name] = str(text)
            if description := value.get(NodeParamsNames.description):
                data[NodeParamsNames.description.name] = description
            if choices := value.get(NodeParamsNames.choices):
                data[NodeParamsNames.choices.name] = choices
            result[key] = RequestParam(**data)
        return result


@dataclass
class Structure:
    http_requests: dict[str, Request]
