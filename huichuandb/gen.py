# -*- coding:utf-8 -*-
# @Time : 2022/4/9 11:49 下午
# @Author : huichuan LI
# @File : gen.py
# @Software: PyCharm
# !/usr/bin/env python3
# encoding: utf-8
import os
import json

# 在当前目录下创建
root_path = os.getcwd()

# 目录列表

# 子文件
children = '{"name": "%s.py", "children": [], "type": "file"}'

# 目录结构
dir_map = [{
    # name 为模块的名字，建议用 syldb 命名，方便后续的实验与课程同步
    'name': "huichuandb",
    'type': 'dir',
    'children': [
        json.loads(children % '__init__'),
        json.loads(children % '__main__'),
        {
            'name': 'case',
            'type': 'dir',
            'children': [json.loads(children % '__init__')]
        },
        {
            'name': 'parse',
            'type': 'dir',
            'children': [json.loads(children % '__init__')]
        },
        {
            'name': 'exceptions',
            'type': 'dir',
            'children': [json.loads(children % '__init__')]
        },
        {
            'name': 'core',
            'type': 'dir',
            'children': [
                json.loads(children % '__init__'),
                json.loads(children % 'database'),
                json.loads(children % 'table'),
                json.loads(children % 'field')
            ]
        }
    ]
}]


# 创建文件夹或者文件
def create(path, kind):
    if kind == 'dir':
        os.mkdir(path)
    else:
        open(path, 'w').close()


# 递归创建目录
def gen_project(parent_path, map_obj):
    for line in map_obj:
        path = os.path.join(parent_path, line['name'])
        create(path, line['type'])
        if line['children']:
            gen_project(path, line['children'])


# 脚本入口
def main():
    gen_project(root_path, dir_map)


if __name__ == '__main__':
    main()
