import os

from syldb.core import SerializedInterface
from syldb.core.field import Field
from syldb.handle.dataHandle import encode_data, decode_data


class Page(SerializedInterface):
    """
    数据页对象
    """
    def __init__(self, path='', is_new=False, **options):
        """
        页对象初始化
        :param path: 数据页存储路径
        :param is_new: 是否为新建页，默认为否
        :param options: 表字段映射，非新建页时为空
        """
        self.__field_names = []  # 字段名列表
        self.__field_objs = {}  # 字段对象映射
        self.__rows = 0  # 页数据大小
        self.__path = path  # 页存储路径

        if 'options' in options.keys():
            # 提取参数
            options = options['options']

        for field_name, field_obj in options.items():
            # 为页对象添加字段
            self.add_field(field_name, field_obj)

        if is_new:
            # 提交页
            self.__dump_page()

        self.__load_page()  # 加载页

    def add_field(self, field_name, field_obj, value=None):
        """
        添加字段
        :param value: 字段默认值，默认为空
        :param field_name: 字段名
        :param field_obj: 字段对象
        :return:
        """
        if field_name in self.__field_names:
            # 字段必须唯一，若字段存在，则抛出字段已存在异常
            raise Exception('Field is exist.')

        if not isinstance(field_obj, Field):
            # 判断字段类型，若字段类型与字段对象不匹配，抛出字段类型异常
            raise TypeError('Field type is except, Field value must be Field object.')

        self.__field_names.append(field_name)  # 添加字段名
        self.__field_objs[field_name] = field_obj  # 绑定字段名与字段

        # 若已存在其他字段，则同步字段为等长，若无，则初始化数据长度为第一个字段数据长度
        if len(self.__field_names) > 1:
            length = self.__rows
            field_obj_length = field_obj.length()

            # 若新增字段本身包含数据，则判断长度是否与已有字段长度相等
            if field_obj_length != 0:
                if field_obj_length == length:
                    return
                raise Exception('data length is not match.')

            # 循环初始化新增字段数据，直到新增字段数据长度与已存在字段的数据长度相等
            for _ in range(0, length):
                if value:
                    self.get_field_obj(field_name).add(value)
                else:
                    self.get_field_obj(field_name).add(None)
        else:
            self.__rows = field_obj.length()
        self.__dump_page()

    def get_field_obj(self, field_name):
        """
        获取字段对象
        :param field_name: 字段名
        :return: 数据字段对象
        """
        if field_name not in self.__field_names:
            raise Exception(f'{field_name} is not exist.')
        return self.__field_objs[field_name]

    def get_size(self):
        """
        获取数据页大小
        :return: 数据页的数据量
        """
        field = self.get_field_obj(self.__field_names[0])
        return field.length()

    def get_path(self):
        """
        获取数据页存储路径
        :return: 数据页存储路径
        """
        return self.__path

    def get_field_data(self, field_name, index=None):
        """
        获取字段数据
        :param field_name: 字段名称
        :param index: 目标数据的位置索引
        :return: 目标字段数据
        """
        field = self.get_field_obj(field_name)
        return field.get_data(index)

    def get_data(self):
        """
        获取页数据
        :return: 页对象中包含的所有字段数据
        """
        data = {}
        for field_name in self.__field_objs.keys():
            data[field_name] = self.get_field_data(field_name)
        return data

    def increment_length(self):
        """
        自增数据长度
        :return:
        """
        self.__rows += 1

    def serialized(self):
        """
        序列化对象
        :return: 序列化后的数据
        """
        data = {}  # 初始化数据字典
        for field in self.__field_names:
            data[field] = self.__field_objs[field].serialized()
        return SerializedInterface.json.dumps(data)

    def deserialized(self, data):
        """
        反序列化对象
        :param data: 待反序列化数据
        :return:
        """
        # 将数据转化为 json 对象
        json_data = SerializedInterface.json.loads(data)

        field_names = [field_name for field_name in json_data.keys()]

        for field_name in field_names:
            # 遍历所有对象，然后反序列化 Field 对象，再添加到 Page 对象中
            field_obj = Field.deserialized(json_data[field_name])
            self.__field_names.append(field_name)
            self.__field_objs[field_name] = field_obj

    def commit(self):
        """
        提交页对象改动
        :return:
        """
        self.__dump_page()

    def rollback(self):
        """
        回滚页改动
        :return:
        """
        self.__load_page()

    def __dump_page(self):
        """
        保存数据页到磁盘
        """
        path = self.__path + '.data'

        with open(path, 'wb') as f:
            content = encode_data(self.serialized())
            f.write(content)

    def __load_page(self):
        """
        从磁盘中加载数据页
        """
        path = self.__path + '.data'
        if not os.path.exists(path):
            raise Exception('page save path is not exist.')

        with open(path, 'rb') as f:
            content = f.read()

        if content:
            self.deserialized(decode_data(content))
