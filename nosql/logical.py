# -*- coding:utf-8 -*-
# @Time : 2022/4/7 12:27 上午
# @Author : huichuan LI
# @File : logical.py
# @Software: PyCharm
import os
import struct


class Storage(object):
    SUPERBLOCK_SIZE = 4096
    INTEGER_FORMAT = "!Q"
    INTEGER_LENGTH = 8

