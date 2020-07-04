#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'Gz'
from basics_function.golable_function import config_data_path
from basics_function.Inspection_method import InspectionMethod
from urllib.parse import urlencode
import json
import requests


class ApiTester:
    def __init__(self, config, source="online"):
        self.inspection_method = InspectionMethod()
        self.config = config["data"]
        self.source = self.config["SOURCE"][source]
        self.headers_data = self.source["HEADERS"]
        self.url = self.source["URL"]
        self.params = self.source["PARAMS"]
        self.request_mode = self.source["MODE"]["TYPE"]
        self.request_body = self.source["BODY"]
        self.body_type = self.request_body["TYPE"]
        self.body_data = self.request_body["DATA"]
        self.assert_data_format = self.config["DATA_FORMAT"]
        self.assert_data_content = self.config["DATA_CONTENT"]
        self.fail_list = []
        self.response = None

    def get_headers(self):
        header_type = self.headers_data["TYPE"]
        headers_data = self.headers_data["DATA"]
        if header_type == "NORMAL":
            return headers_data

    def get_url(self):
        url_type = self.params["TYPE"]
        params_data = self.params["DATA"]
        if params_data is None:
            return self.url
        if url_type == "JOIN":
            return self.url + "?" + urlencode(params_data)

    def get_body(self):
        if self.request_mode == "GET":
            return None
        if self.request_mode == "POST" and self.body_type == "JSON":
            return json.dumps(self.body_data)

    def api_assert(self, response, request_data):
        if response.status_code == 200:
            response_code_result = True
        else:
            response_code_result = False
            self.fail_list.append({"request_data": request_data, "response": response.text})
        try:
            response_json = json.loads(response.text)
        except Exception as e:
            print("Json 解析错误", e)
            response_json = False
            self.fail_list.append({"request_data": request_data, "response": response.text})
        if self.assert_data_format is not None and response_code_result and response_json:
            format_result = self.inspection_method.structure_format_diff(self.assert_data_format, response_json)
            if format_result is False:
                self.inspection_method.fail_list_assert()
            else:
                self.inspection_method.fail_list = []

    def error_message(self):
        for fail in self.fail_list:
            print("Headers:", fail["request_data"]["headers"])
            print("Url:", fail["request_data"]["url"])
            print("Body:", fail["request_data"]["body"])
            print("Mode:", self.request_mode)
            print("Response:", fail["response"])

    def api_test(self):
        headers = self.get_headers()
        url = self.get_url()
        body = self.get_body()
        requests_data = {"headers": headers, "url": url, "body": body}
        if self.request_mode == "GET":
            response = requests.get(url, headers=headers)
        else:
            if self.body_type == "JSON":
                response = requests.post(url, json=body)
        self.response = response
        self.api_assert(response, requests_data)


def single_api_tester(yaml_path, source="online"):
    config = config_data_path(yaml_path)
    a = ApiTester(config)
    a.api_test()
    if len(a.fail_list) > 0:
        return False
    else:
        return True


if __name__ == "__main__":
    single_api_tester("./../case/all/verity_roomtype.yml")
