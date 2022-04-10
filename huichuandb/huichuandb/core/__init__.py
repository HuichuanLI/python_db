from enum import Enum

import json


class SerializedInterface:
    json = json

    @staticmethod
    def deserialized(obj):
        raise NotImplementedError

    def serialized(self):
        raise NotImplementedError


# 字段类型枚举
class FieldType(Enum):
    INT = int = 'int'  # 整型
    VARCHAR = varchar = 'str'  # 字符型
    FLOAT = float = 'float'  # 浮点型


# 数据类型映射
TYPE_MAP = {
    'int': int,
    'float': float,
    'str': str,
    'INT': int,
    'FLOAT': float,
    'VARCHAR': str
}


# 字段主键枚举
class FieldKey(Enum):
    PRIMARY = 'PRIMARY KEY'  # 主键约束
    INCREMENT = 'AUTO_INCREMENT'  # 自增约束
    UNIQUE = 'UNIQUE'  # 唯一约束
    NOT_NULL = 'NOT NULL'  # 非空约束
    NULL = 'NULL'  # 可空约束，作为默认的约束使用
