from huichuandb.core import FieldKey, FieldType, TYPE_MAP
from huichuandb.core import SerializedInterface


# 数据字段对象
class Field(SerializedInterface):
    def __init__(self, data_type, keys=FieldKey.NULL, default=None):
        self.__type = data_type  # 字段的数据类型
        self.__keys = keys  # 字段的数据约束
        self.__default = default  # 默认值
        self.__values = []  # 字段数据
        self.__rows = 0  # 字段数据长度

        # 如果约束只有一个，并且非 list 类型，则转换为 list
        if not isinstance(self.__keys, list):
            self.__keys = [self.__keys]

        # 如果类型不属于 FieldType，抛出异常
        if not isinstance(self.__type, FieldType):
            raise TypeError('Data-Type require type of "FieldType"')

        # 如果类型不属于 FieldKey，抛出异常
        for key in self.__keys:
            if not isinstance(key, FieldKey):
                raise TypeError('Data-Key require type of "FieldKey"')

        # 如果有自增约束，判断数据类型是否为整型和是否有主键约束
        if FieldKey.INCREMENT in self.__keys:
            # 如果不是整型，抛出类型错误异常
            if self.__type != FieldType.INT:
                raise TypeError('Increment key require Data-Type is integer')

            # 如果没有主键约束，抛出无主键约束异常
            if FieldKey.PRIMARY not in self.__keys:
                raise Exception('Increment key require primary key')

        # 如果默认值不为空并且设置了唯一约束，抛出唯一约束不能设置默认值异常
        if self.__default is not None and FieldKey.UNIQUE in self.__keys:
            raise Exception('Unique key not allow to set default value')
