from dataclasses import dataclass, field
import re


class ParamTypes:
    url = 1
    query = 2
    body = 3
    header = 4


@dataclass
class RequestParam:
    choices: list = field(default_factory=list)
    text: str = None
    description: str = ""
    param_type: int = 0         # 1: part of url, 2: query parameter, 3: body parameter, 4: header
    current_value: str = None   # should be set after user commands to send request.


@dataclass
class Request:
    name: str
    url: str
    method: str
    headers: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)
    query_params: dict = field(default_factory=dict)
    # all adjustable parameters including URL parts is curl braces, query parameters, headers and body parameters:
    params: dict[str, RequestParam] = field(init=False)

    def __post_init__(self):
        self.params = {}
        url_keys = re.findall(r"\{.*?}", self.url)
        for item in url_keys:
            kv = item.strip("{}")
            self.params[kv] = RequestParam(text=kv, param_type=ParamTypes.url)
        self._prepare_params(self.body, ParamTypes.body)
        self._prepare_params(self.query_params, ParamTypes.query)
        self._prepare_params(self.headers, ParamTypes.header)

    def _prepare_params(self, params: dict, param_type: int):
        for key, value in params.items():
            data = dict(param_type=param_type)
            if text := value.get("text"):
                data["text"] = str(text)
            if description := value.get("description"):
                data["description"] = description
            if choices := value.get("choices"):
                data["choices"] = choices
            self.params[key] = RequestParam(**data)


@dataclass
class Structure:
    http_requests: dict[str, Request]