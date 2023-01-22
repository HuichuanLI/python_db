import json
from enum import Enum


class SerializedInterface:
    """
    序列化与反序列化接口
    """
    json = json

    def __init__(self):
        self.json = json  # 内部定义一个 json 对象，方便后续操作，减少 import

    # 反序列化方法
    @staticmethod
    def deserialized(obj):
        raise NotImplementedError  # 抛出未实现异常

    # 序列化方法
    def serialized(self):
        raise NotImplementedError  # 抛出未实现异常


class FieldType(Enum):
    """
    字段类型枚举类
    """
    INT = int = 'int'  # 整型
    VARCHAR = varchar = 'str'  # 字符型
    FLOAT = float = 'float'  # 浮点型


# 字段类型映射
TYPE_MAP = {
    'int': int,
    'float': float,
    'str': str,
    'INT': int,
    'FLOAT': float,
    'VARCHAR': str
}


class FieldKey(Enum):
    """
    字段约束枚举类
    """
    PRIMARY = 'PRIMARY KEY'  # 主键约束
    INCREMENT = 'AUTO_INCREMENT'  # 自增约束
    UNIQUE = 'UNIQUE'  # 唯一约束
    NOT_NULL = 'NOT NULL'  # 非空约束
    NULL = 'NULL'  # 可空约束，作为默认的约束使用
