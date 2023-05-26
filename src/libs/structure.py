from dataclasses import dataclass, field, MISSING
from enum import Enum   # ToDo: change to TextEnum after switching to Python 3.11
import re
from typing import Any


TEMPLATE_TO_FIND_URL_PARTS = r"\{(.*?)}"
TEMPLATE_TO_SPLIT_URL = r"\{.*?}"
TEMPLATE_TO_REPLACE_PARAM = r'"{{{%s}}}"'
HTTP_LOG = "http_log.txt"


def _empty_value():
    return MISSING


def _to_string(value: Any) -> str:
    match value:
        case None:
            return "null"
        case bool():
            return str(value).lower()
        case _:
            return str(value)


######## Names enums ################

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
    choices = "choices"
    description = "description"
    text = "text"


class RequestSectionParamsNames(str, Enum):
    keys = "keys"
    json = "json"


class GeneralParamsNames(str, Enum):
    enable_http_log = "enable_http_log"
    http_log = "http_log"


class TypeNames(Enum):
    string = "string"
    boolean = "boolean"
    number = "number"
    null = "null"
    empty = MISSING


########### Data classes ##############

@dataclass
class General:
    enable_http_log: bool = False
    http_log: str = HTTP_LOG


@dataclass
class RequestParam:
    choices: [list, TypeNames.empty.value] = field(default_factory=_empty_value)
    text: [str, TypeNames.empty.value] = field(default_factory=_empty_value)
    description: [str, TypeNames.empty.value] = field(default_factory=_empty_value)
    type: str = field(default_factory=_empty_value)
    current_value: [str, TypeNames.empty.value] = field(default_factory=_empty_value)   # should be set after a user commands to send request.

    def __post_init__(self):
        if self.text is not MISSING:  # support of boolean params in text area
            match self.text:
                case bool():
                    self.choices = [_to_string(self.text), _to_string(not self.text)]
                    self.text = MISSING
                case _:
                    self.text = _to_string(self.text)
        if self.description is not MISSING:
            self.description = str(self.description)
        if not isinstance(self.choices, list):
            self.choices = MISSING
        if self.choices is not MISSING:
            self.choices = list(map(_to_string, self.choices))
        if self.type is not MISSING:
            if self.type not in [x.value for x in TypeNames]:
                self.type = TypeNames.string.value


@dataclass
class RequestSection:
    json: dict = field(default_factory=dict)    # mandatory section - contains section data
    keys: dict = field(default_factory=dict)    # optional section - contains adjustable parameters
    parsed_keys: dict[str, RequestParam] = field(init=False)

    def __post_init__(self):
        self.parsed_keys = {}
        for key, value in self.keys.items():
            data = RequestParam(**value)
            self.parsed_keys[key] = data


@dataclass
class Request:
    name: str
    url: str
    method: str
    # all sections including URL parts in curl braces, query parameters and headers:
    body: RequestSection = field(default_factory=RequestSection)
    headers: RequestSection = field(default_factory=RequestSection)
    query_params: RequestSection = field(default_factory=RequestSection)
    parsed_url_parts: list[RequestParam] = field(init=False)

    def __post_init__(self):
        self.parsed_url_parts = []
        url_keys = re.findall(TEMPLATE_TO_FIND_URL_PARTS, self.url)
        for item in url_keys:
            self.parsed_url_parts.append(RequestParam(text=item))


@dataclass
class Structure:
    http_requests: dict[str, Request]
    general: General = field(default_factory=General)
