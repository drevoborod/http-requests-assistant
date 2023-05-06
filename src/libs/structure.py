from dataclasses import dataclass, field
from enum import Enum   # ToDo: change to TextEnum after switching to Python 3.11
import re


TEMPLATE_TO_FIND_URL_PARTS = r"\{(.*?)}"
TEMPLATE_TO_SPLIT_URL = r"\{.*?}"
TEMPLATE_TO_REPLACE_PARAM = r'{{{%s}}}'
HTTP_LOG = "http_log.txt"


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

########### Data classes ##############

@dataclass
class General:
    enable_http_log: bool = False
    http_log: str = HTTP_LOG


@dataclass
class RequestParam:
    choices: list = field(default_factory=list)
    text: str = None
    description: str = ""
    current_value: str = None   # should be set after a user commands to send request.


@dataclass
class RequestSection:
    json: dict = field(default_factory=dict)    # mandatory section - contains section data
    keys: dict = field(default_factory=dict)    # optional section - contains adjustable parameters
    parsed_keys: dict[str, RequestParam] = field(init=False)

    def __post_init__(self):
        self.parsed_keys = {}
        for key, value in self.keys.items():
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
            self.parsed_keys[key] = RequestParam(**data)


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
