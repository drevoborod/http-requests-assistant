from dataclasses import dataclass, field
import re


@dataclass
class RequestParam:
    choices: list = field(default_factory=list)
    text: str = None
    description: str = ""


@dataclass
class Request:
    name: str
    url: str
    method: str
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

    def __getattr__(self, item):
        if not hasattr(self, item):
            return None
        return getattr(self, item)


@dataclass
class Structure:
    http_requests: dict[str, Request]