#!/usr/bin/env python3

import json
import sys
from pathlib import Path
import re

import yaml

from libs.structure import NodeParamsNames, RequestParamsNames, RootParamsNames


POSTMAN_SCHEMA_STRING_TEMPLATE = re.compile(r"https://schema\..*postman\.com/.*/(v\d[0-9.]*)/.*\.json")
SUPPORTED_POSTMAN_SCHEME = ["v2.1.0", "v2.0.0"]
POSTMAN_RESULT_FILE_NAME = "postman.yml"


def load_json_file(file_path: str) -> (bool, [str, dict]):
    path = Path(file_path)
    try:
        data = json.load(path.open())
    except Exception as e:
        return False, e
    else:
        return True, data


def _convert_postman_request(data: dict) -> dict:
    request = data["request"]
    result = {
        RequestParamsNames.name.value: data["name"],
        RequestParamsNames.method.value: request["method"]
    }

    url_source = request["url"]
    if isinstance(url_source, str):
        result[RequestParamsNames.url.value] = url_source
    else:
        url = [url_source["protocol"] + ":/"]
        url.append(".".join(url_source["host"]))
        url.append("/".join(url_source["path"]))
        result[RequestParamsNames.url.value] = "/".join(url)

    if isinstance(url_source, dict):
        if query_source := url_source.get("query"):
            result[RequestParamsNames.query_params.value] = {item["key"]: {NodeParamsNames.text.value: item["value"]} for item in query_source}

    headers_source = request.get("header")
    if headers_source:
        result[RequestParamsNames.headers.value] = {item["key"]: {NodeParamsNames.text.value: item["value"]} for item in headers_source}

    body_source = request.get("body")
    # Only JSON body supported yet:
    if body_source and body_source["mode"] == "raw":
        try:
            parsed_body = json.loads(body_source["raw"])    # should be dictionary
        except Exception:
            # ToDO: add logging here
            pass
        else:
            result[RequestParamsNames.body.value] = {}
            for key, value in parsed_body.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                result[RequestParamsNames.body.value][key] = {NodeParamsNames.text.value: value}

    return result


def convert_postman_collection(data: dict) -> (bool, [str, dict]):
    error_message = "It's not a valid Postman collection."
    if info := data.get("info"):
        schema_string = info.get("schema")
        if not schema_string:
            return False, error_message
    else:
        return False, error_message
    schema_match = POSTMAN_SCHEMA_STRING_TEMPLATE.fullmatch(schema_string)
    if not schema_match:
        return False, error_message + " Invalid schema path."
    if schema_match.group(1) not in SUPPORTED_POSTMAN_SCHEME:
        return False, error_message + " Unsupported schema version."
    result = {RootParamsNames.http_requests.value: {}}
    for number, request in enumerate(data["item"], start=1):
        result[RootParamsNames.http_requests.value][f"request{number}"] = _convert_postman_request(request)
    return True, result


if __name__ == '__main__':
    p = sys.argv[1]
    parsed = load_json_file(p)
    if not parsed[0]:
        sys.exit(f"Unable to load JSON file.\n{parsed[1]}")
    converted = convert_postman_collection(parsed[1])
    if not converted[0]:
        sys.exit(converted[1])
    with open(POSTMAN_RESULT_FILE_NAME, "w") as file:
        yaml.dump(converted[1], file, sort_keys=False, indent=4, allow_unicode=True)
