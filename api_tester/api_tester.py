#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'Gz'
from basics_function.golable_function import config_reader, assert_function_import, params_function_import, \
    header_function_import, body_function_import, above_function_import, get_key_value_list
from basics_function.Inspection_method import InspectionMethod
from urllib.parse import urlencode
import json
import requests
import os

PATH = os.path.dirname(os.path.abspath(__file__))


def change_keys_value(base_data, keys, value):
    if isinstance(keys, str):
        keys = keys.split("/")
    key = keys.pop(0)
    if isinstance(base_data[key], dict):
        base_data[key] = change_keys_value(base_data[key], keys, value)
    else:
        base_data[key] = value
    return base_data


class ApiTester:
    def __init__(self, config, source="online"):
        self.env_config = None
        self.source_name = source
        self.inspection_method = InspectionMethod()
        self.case_data = config
        if self.case_data["ENV_DATA"] is not None and self.source_name in self.case_data["ENV_DATA"].keys():
            self.env_data = self.case_data["ENV_DATA"][self.source_name]
            self.host = self.env_data["HOST"]
        else:
            self.env_data = None
            self.host = None
        if "CONFIG" in self.case_data:
            self.case_config = self.case_data["CONFIG"]
            if "ASSERT" in self.case_config.keys():
                self.case_assert_config = self.case_config["ASSERT"]
            else:
                self.case_assert_config = None
        else:
            self.case_config = None
            self.case_assert_config = None
        self.assert_config()
        self.url_path = self.case_data["SOURCE"]["URL_PATH"]
        self.source = self.case_data["SOURCE"][self.source_name]
        self.url = self.case_data["SOURCE"][self.source_name]["URL"]
        self.headers = self.source["HEADERS"]
        self.headers_type = self.headers["TYPE"]
        self.headers_data = self.headers["DATA"]
        self.params = self.source["PARAMS"]
        self.params_type = self.params["TYPE"]
        self.params_data = self.params["DATA"]
        self.request_mode = self.case_data["SOURCE"]["METHOD"]
        self.request_body = self.source["BODY"]
        self.body_type = self.request_body["TYPE"]
        self.body_data = self.request_body["DATA"]
        self.assert_data_format = self.case_data["ASSERT"]["DATA_FORMAT"]
        try:
            self.assert_data_format_data = self.case_data["ASSERT"]["DATA_FORMAT"]["DATA"]
        except:
            self.assert_data_format_data = None
        try:
            self.assert_data_content = self.case_data["ASSERT"]["DATA_CONTENT"][self.source_name]
        except:
            self.assert_data_content = None
        self.another_assert_data = self.case_data["ASSERT"]["ANOTHER_ASSERT"]
        try:
            self.another_assert_data_source = self.case_data["ASSERT"]["ANOTHER_ASSERT"][self.source_name]
        except:
            self.another_assert_data_source = None
        self.another_assert_fail_list = []
        self.fail_list = []
        self.response = None
        self.the_url = None
        self.the_headers = None
        self.the_body = None
        # 上线文数据处理
        self.above_response = None
        if "ABOVE" in self.case_data.keys():
            self.above_way = self.case_data["ABOVE"]
        else:
            self.above_way = None

    def assert_config(self):
        if self.case_data["ENV_DATA"] is not None:
            self.env_config = self.case_data["ENV_DATA"]["CONFIG"]
        if self.env_config is not None and "ASSERT" in self.env_config and self.case_assert_config is None:
            self.case_assert_config = self.env_config["ASSERT"]
        if self.case_assert_config is not None:
            for k, v in self.case_assert_config.items():
                self.inspection_method.extra[k] = v

    def get_headers(self):
        if self.headers_type == "NORMAL":
            return self.headers_data
        headers_func = header_function_import(self.headers_type)
        return headers_func(func_data=self.headers_data, case_data=self.case_data, source_name=self.source_name)

    def get_url(self):
        if self.host is not None and self.url_path is not None:
            self.url = self.host + self.url_path
        if self.params_data is None:
            return self.url
        if self.params_type == "JOIN":
            return self.url + "?" + urlencode(self.params_data)
        params_func = params_function_import(self.params_type)
        return params_func(func_data=self.params_data, case_data=self.case_data, source_name=self.source_name)

    def get_body(self):
        if self.request_mode == "GET":
            return None
        if self.request_mode == "POST" and self.body_type == "JSON" or self.body_type == "DATA":
            return json.dumps(self.body_data)
        body_func = body_function_import(self.body_type)
        self.body_type = "JSON"
        return body_func(func_data=self.body_data, case_data=self.case_data, source_name=self.source_name)

    def format_assert(self):
        if self.response.status_code == 200:
            response_code_result = True
        else:
            response_code_result = False
            msg = "请求结果非200,Code为:{}".format(str(self.response.status_code))
            self.fail_list.append({"reason": msg, "case": None, "response": self.response.text})
        if self.assert_data_format is not None and self.assert_data_format_data is not None and response_code_result:
            format_result = self.inspection_method.structure_format_diff(self.assert_data_format, self.response)
            if format_result is False:
                self.inspection_method.fail_list_assert()
                self.inspection_method.fail_list = []
            else:
                self.inspection_method.fail_list = []

    def content_assert(self):
        if self.assert_data_content is not None and self.inspection_method.response_content_check(
                self.assert_data_content, self.response) is False:
            self.inspection_method.fail_list_assert()
            self.inspection_method.fail_list = []
        else:
            self.inspection_method.fail_list = []

    def another_assert(self):
        if self.another_assert_data is None or self.another_assert_data_source is None:
            return
        if isinstance(self.another_assert_data_source, list):
            for assert_data in self.another_assert_data:
                function_name = assert_data["TYPE"]
                function_data = assert_data["DATA"]
                func = assert_function_import(function_name)
                func(func_data=function_data, case_data=self.case_data, response=self.response,
                     fail_list=self.another_assert_fail_list, source_name=self.source_name)
        else:
            function_name = self.another_assert_data["TYPE"]
            function_data = self.another_assert_data["DATA"]
            func = assert_function_import(function_name)
            func(func_data=function_data, case_data=self.case_data, response=self.response,
                 fail_list=self.another_assert_fail_list, source_name=self.source_name)

    def another_assert_report(self):
        msg = ""
        if len(self.another_assert_fail_list) > 0:
            for i in self.another_assert_fail_list:
                msg = "\n" + msg + i + "\n"
                msg = msg + "\n"
            assert False, msg

    def error_message(self):
        for fail in self.fail_list:
            print("Headers:", fail["request_data"]["headers"])
            print("Url:", fail["request_data"]["url"])
            print("Body:", fail["request_data"]["body"])
            print("Mode:", self.request_mode)
            print("Response:", fail["response"])

    def normal_api_test(self):
        url = self.get_url()
        headers = self.get_headers()
        body = self.get_body()
        if self.request_mode == "GET":
            response = requests.get(url=url, headers=headers)
        else:
            if self.body_type == "JSON":
                response = requests.post(url=url, headers=headers,
                                         json=body)
            else:
                response = requests.post(url=url, headers=headers,
                                         data=body)
        self.response = response
        self.the_url = url
        self.the_headers = headers
        self.the_body = url

    def above_response_to(self, data):
        keys = data["DATA"].split("/")
        data_to = data["TO"]
        above_json = json.loads(self.above_response.text)
        value = get_key_value_list(keys, above_json)
        assert value, "上文参数获取错误,\n" \
                      "层级信息:{} \n" \
                      "上文信息:{}\n".format(str(keys), above_json)
        for k, v in data_to.items():
            if k == "PARAMS":
                change_keys_value(self.params_data, v, value)
            elif k == "BODY":
                change_keys_value(self.body_data, v, value)
            else:
                change_keys_value(self.headers_data, v, value)

    def above_headers_to(self, data):
        keys = data["DATA"].split("/")
        data_to = data["TO"]
        above_header = self.above_response.headers
        value = get_key_value_list(keys, above_header)
        assert value, "上文参数获取错误,\n" \
                      "层级信息:{} \n" \
                      "上文信息:{}\n".format(str(keys), above_header)
        for k, v in data_to.item():
            if k == "PARAMS":
                change_keys_value(self.params_data, v, value)
            if k == "BODY":
                change_keys_value(self.body_data, v, value)
            else:
                change_keys_value(self.headers_data, v, value)

    def deal_with_above(self):
        for result in self.above_way:
            data_from = result["FROM"]
            data_type = result["TYPE"]
            if data_from == "HEADERS" and data_type == "ALL":
                self.headers_data = self.above_response.headers
                self.headers_type = "NORMAL"
                continue
            if data_from == "HEADERS" and data_type == "KEYS":
                self.above_headers_to(result)
                continue
            if data_from == "BODY" and data_type == "KEYS":
                self.above_response_to(result)
                continue
            func = above_function_import(data_type)
            func(self.case_data, source_name=self.source_name)

    def api_test(self):
        if self.above_way is None:
            self.normal_api_test()
        else:
            self.deal_with_above()
            self.normal_api_test()
