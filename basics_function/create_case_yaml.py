#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "Gz"
import yaml
import os
from basics_function.golable_function import config_reader

PATH = os.path.dirname(os.path.abspath(__file__))


def dir_list(path, all_files):
    file_list = os.listdir(path)
    for filename in file_list:
        filepath = os.path.join(path, filename)
        if os.path.isdir(filepath):
            dir_list(filepath, all_files)
        else:
            all_files.append(filepath)
    return all_files


def select_case_folder(options):
    if options == "all_cases":
        result = []
        path = PATH + "/../case"
        return dir_list(path, result)
    else:
        return case_list(options)


def case_list(folder_name):
    folder_path = PATH + "/../case/" + folder_name
    folder_list = []
    try:
        dir_list(folder_path, folder_list)
    except Exception as e:
        print(e)
        print("文件夹填写错误")
        assert False
    result = [folder for folder in folder_list]
    return result


def add_case(case, source):
    case_result = {}
    file_data = config_reader(case)
    try:
        url_path = file_data["SOURCE"]["URL_PATH"]
        if url_path is None:
            url_path = case.split("/")[-1]
    except:
        url_path = case.split("/")[-1]
    # temp_server 中网站相关的判断属于临时处理 web 地址的暂时不进行测试"
    if ("!" not in case) and ("example" not in case) and (".DS_Store" not in case) and ("web" not in case):
        case_result.update({case: {"path": case, "source": source, "api": url_path}})
        return {case: {"path": case, "source": source, "api": url_path}}
    else:
        return {}


def create_case_list(folder_name, source="online"):
    case_result = {}
    case_list_data = select_case_folder(folder_name)
    for case in case_list_data:
        if ((folder_name == "all_cases") and ("_all_" not in case)) or (
                folder_name != "all_cases"):
            case_result.update(add_case(case, source))
    if os.path.exists(PATH + "/../temp/") is False:
        os.mkdir(PATH + "/../temp/")
    with open(PATH + "/../temp/cases.yaml", "w") as case:
        yaml.dump(case_result, case, default_flow_style=False)


if __name__ == "__main__":
    create_case_list("all")
