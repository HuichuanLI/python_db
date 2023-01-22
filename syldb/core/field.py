from syldb.core import FieldKey, FieldType, TYPE_MAP
from syldb.core import SerializedInterface


class Field(SerializedInterface):
    """
    数据库字段对象
    """
    def __init__(self, data_type, keys=FieldKey.NULL, default_value=None):
        self.__type = data_type  # 字段的数据类型
        self.__keys = keys  # 字段的数据约束
        self.__default_value = default_value  # 默认值
        self.__values = []  # 字段数据
        self.__rows = 0  # 字段数据长度

        self.__init_check()  # 初始化检查

    def __init_check(self):
        # 如果约束只有一个，并且非 list 类型，则转换为 list
        if not isinstance(self.__keys, list):
            self.__keys = [self.__keys]

        # 如果类型不属于 FieldType，抛出异常
        if not isinstance(self.__type, FieldType):
            raise TypeError(f'Data-Type require type of {FieldType}')

        # 如果类型不属于 FieldKey，抛出异常
        for key in self.__keys:
            if not isinstance(key, FieldKey):
                raise TypeError(f'Data-Key require type of {FieldKey}')

        # 如果有自增约束，判断数据类型是否为整型和是否有主键约束
        if FieldKey.INCREMENT in self.__keys:
            # 如果不是整型，抛出类型错误异常
            if self.__type != FieldType.INT:
                raise TypeError('Increment key require Data-Type is integer')

            # 如果没有主键约束，抛出无主键约束异常
            if FieldKey.PRIMARY not in self.__keys:
                raise Exception('Increment key require primary key')

        # 如果默认值不为空并且设置了唯一约束，抛出唯一约束不能设置默认值异常
        if self.__default_value is not None and FieldKey.UNIQUE in self.__keys:
            raise Exception('Unique key not allow to set default value')

    def __check_type(self, value):
        """
        数据类型检查
        :param value: 待插入数据
        :return:
        """
        # 如果该值的类型不符合定义好的类型，抛出类型错误异常
        if value is not None and not isinstance(value, TYPE_MAP[self.__type.value]):
            raise TypeError(f'data type error, value type must be {self.__type}')

    def __check_index(self, index):
        """
        数据指定位置索引检查
        :param index: 数据位置索引
        :return:
        """
        # 如果指定位置不存在，抛出不存在该元素异常
        if not isinstance(index, int) or not -index < self.__rows or index > self.__rows:
            raise Exception('Not this element')

        return True

    def __check_key(self, value):
        """
        字段值约束检查
        :param value: 字段值
        :return: 通过检查的字段值
        """
        # 如果字段包含自增键，则选择合适的值自动自增
        if FieldKey.INCREMENT in self.__keys:
            # 如果值为空，则用字段数据长度作为基值自增
            if value is None:
                value = self.__rows + 1

            # 如果值已存在，则抛出一个值已经存在的异常
            if value in self.__values:
                raise Exception(f'value {value} exists')

        # 如果字段包含主键约束或者唯一约束，判断值是否存在
        if FieldKey.PRIMARY in self.__keys or FieldKey.UNIQUE in self.__keys:
            # 如果值已存在，抛出存在异常
            if value in self.__values:
                raise Exception(f'value {value} exists')

        # 如果该字段包含主键或者非空键，并且添加的值为空值，则抛出值不能为空异常
        if (FieldKey.PRIMARY in self.__keys or FieldKey.NOT_NULL in self.__keys) and value is None:
            raise Exception('field value is not null')

        return value

    def get_real_index(self, value):
        """
        获取实际索引位置
        :param value: 待获取索引位置的值
        :return:
        """
        return self.__values.index(value) if value in self.__values else 0

    def length(self):
        """
        获取数据数量
        :return: 数据数量
        """
        return self.__rows

    def get_keys(self):
        """
        获取数据约束
        :return: 数据约束
        """
        return self.__keys

    def get_type(self):
        """
        获取数据类型
        :return: 数据类型
        """
        return self.__type

    def get_data(self, index=None):
        """
        获取数据
        :param index: 目标数据的位置索引
        :return: 满足条件的所有数据
        """
        if index is not None and self.__check_index(index):
            # 若索引参数存在，且索引位置正确，则直接返回指定索引数据
            return self.__values[index]

        # 返回所有数据
        return self.__values

    def check_value(self, value):
        """
        数据检查方法
        :param value: 待检查数据
        :return:
        """
        if not value:
            # 若插入数据为空，则使用默认数据
            if FieldKey.INCREMENT in self.__keys:
                # 如果有自增主键，则自增
                value = self.__rows + 1
            else:
                value = self.__default_value
        value = self.__check_key(value)
        self.__check_type(value)
        return value

    def add(self, value):
        """
        添加数据
        :param value: 待添加的数据
        :return:
        """
        value = self.check_value(value)

        # 数据检查正常，插入数据
        self.__values.append(value)
        self.__rows += 1

    def delete(self, index):
        """
        删除数据
        :param index: 目标数据位置索引
        :return:
        """
        # 如果删除的位置不存在，抛出不存在该元素异常
        self.__check_index(index)
        # 删除数据，并减少数据长度
        self.__values.pop(index)
        self.__rows -= 1

    def modify(self, index, value):
        """
        修改指定位置数据
        :param index: 目标数据位置索引
        :param value: 修改后数据
        :return:
        """
        # 数据检查
        self.__check_index(index)
        value = self.__check_key(value)
        self.__check_type(value)

        # 数据检查正常，修改指定位置索引数据
        self.__values[index] = value

    def serialized(self):
        """
        序列化数据字段对象
        :return: 包含数据字段内容的字符串
        """
        return SerializedInterface.json.dumps({
            'key': [key.value for key in self.__keys],
            'type': self.__type.value,
            'values': self.__values,
            'default_value': self.__default_value
        })

    @staticmethod
    def deserialized(data):
        """
        反序列化为对象
        :param data: 数据字段内容
        :return:
        """
        # 将数据转化为 json 字典
        json_data = SerializedInterface.json.loads(data)

        # 获取数据字段约束为 FieldKey 中的属性
        keys = [FieldKey(key) for key in json_data['key']]

        # 实例化数据字段对象
        obj = Field(data_type=FieldType(json_data['type']), keys=keys, default_value=json_data['default_value'])

        for value in json_data['values']:
            # 为数据字段对象添加数据
            obj.add(value=value)
        return obj  # 返回数据字段对象
