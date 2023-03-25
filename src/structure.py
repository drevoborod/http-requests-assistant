from dataclasses import dataclass, field
import re


URL_PARTS_TEMPLATE = r"\{(.*?)}"


@dataclass
class RequestParam:
    choices: list = field(default_factory=list)
    text: str = None
    description: str = ""
    current_value: str = None   # should be set after user commands to send request.


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
            if (text := value.get("text")) is not None:  # support of boolean params in text area
                if isinstance(text, bool):
                    data["choices"] = [text, not text]
                else:
                    data["text"] = str(text)
            if description := value.get("description"):
                data["description"] = description
            if choices := value.get("choices"):
                data["choices"] = choices
            result[key] = RequestParam(**data)
        return result


@dataclass
class Structure:
    http_requests: dict[str, Request]
