from syldb.core.page import Page
from syldb.conf import Config
from syldb.core.record import Record
from syldb.tools.fileTools import join_path, mkdir, delete_file, is_exists
from syldb.tools.storageTools import dump_obj, load_obj
from syldb.case import BaseCase
from syldb.handle.treeHandle import BPTree
from syldb.core import FieldKey, FieldType


class Table:
    """
    数据表对象
    """

    def __init__(self, db_name, tb_name, is_new=False):
        """
        初始化表对象
        :param db_name: 数据库名称
        :param tb_name: 数据表名称
        :param is_new: 是否新建表
        """
        self.__db_name = db_name  # 数据库名
        self.__name = tb_name  # 当前数据表名
        self.__path = join_path(Config().data_path, self.__db_name, self.__name)  # 数据表存储路径
        self.__page_nums = []  # 数据表包含的存储页的页号
        self.__index_field = {}  # 数据表包含的索引映射
        self.__rows = 0  # 数据表数据长度

        self.page_size = Config().page_size  # 页最大容量

        self.__fields = Record(db_name=self.__db_name).get_table_field(self.__name)  # 数据字段映射

        if is_new and not is_exists(self.__path):
            # 若为创建表，则新建表路径，并创建第一个页
            self.__path = mkdir(self.__path)
            self.create_page(0)
            self.__dump_table()

        self.__load_table()

    def create_page(self, page_num):
        """
        创建页
        :param page_num: 页号
        :return:
        """
        page_num = str(page_num)  # 将页号转换为 str 格式，防止拼接路径时出错
        if self.__check_page_num(page_num):
            # 判断页是否存在
            raise Exception(f'page {page_num} is exists.')

        try:
            options = self.__fields  # 获得表字段
            self.__page_nums.append(page_num)  # 增加页号记录
            path = join_path(self.__path, page_num)  # 拼接数据页路径
            _ = Page(path=path, is_new=True, options=options)  # 创建页对象
            self.__dump_table()  # 保存表
        except Exception as e:
            print(str(e))

    def drop_page(self, page_num):
        """
        删除页
        :param page_num: 页号
        :return:
        """
        page_num = str(page_num)  # 将页号转换为 str 格式，防止拼接路径时出错

        if not self.__check_page_num(page_num):
            # 判断页是否存在
            raise Exception(f'page {page_num} is not exists.')

        self.__page_nums.remove(page_num)  # 删除页号记录
        path = join_path(self.__path, page_num) + '.data'  # 拼接数据页路径
        delete_file(path)  # 删除数据页
        self.__dump_table()  # 保存表

    def create_index(self, index_name, index_field):
        """
        创建索引
        :param index_name: 索引名称
        :param index_field: 索引字段
        :return:
        """
        if index_name in self.__index_field.keys():
            # 索引已经存在
            raise Exception(f'{index_name} is exist.')

        elif index_field in self.__index_field.values():
            raise Exception(f'There is already an index to {index_field}.')

        field = self.__fields[index_field]

        if field.get_type() not in [FieldType.INT, FieldType.FLOAT]:
            # 检查数据类型
            raise Exception(f'The {index_field} data type is not support.')

        keys = field.get_keys()
        primary_key = self.get_primary_key()

        if FieldKey.PRIMARY in keys:
            raise Exception(f'Do not need to create an index for the primary key.')

        if (FieldKey.INCREMENT not in keys) and (FieldKey.NOT_NULL not in keys or FieldKey.UNIQUE not in keys):
            raise Exception(f'The {index_field} field key is incorrect.')

        data = self.get_data()  # 获取全表数据

        keys = data[index_field]  # 获取索引列
        values = data[primary_key]  # 获取主键

        # 创建 B+ 树
        init_tree = BPTree(path=self.__path, index_name=index_name, is_new=True)
        tree = init_tree.make_tree(keys, values)
        if tree is not None:
            self.__index_field[index_name] = index_field
        else:
            raise Exception(f'The {index_name} create fail, please check data.')

        self.__dump_table()

    def drop_index(self, index_name):
        """
        删除索引
        :param index_name: 索引名称
        :return:
        """
        if index_name not in self.__index_field.keys():
            # 索引已经存在
            raise Exception(f'{index_name} is not exist.')

        del self.__index_field[index_name]

        path = join_path(self.__path, index_name + '.idx')
        delete_file(path)
        self.__dump_table()

    def get_primary_key(self):
        """
        获取主键
        :return:
        """
        for field_name, field_obj in self.__fields.items():
            # 遍历所有字段，找出主键
            if FieldKey.PRIMARY in field_obj.get_keys():
                return field_name
        return ''  # 查找失败，返回空字符串，此情况不应存在，数据表必须存在主键

    def get_page_list(self):
        """
        获取所有数据页号
        :return:
        """
        return self.__page_nums

    def get_page_obj(self, page_num):
        """
        获取指定页对象
        :param page_num: 页号
        :return:
        """
        if not self.__page_nums:
            # 若没有页存在，则直接创建当前页
            # 这一操作，是为了给误删所有数据页所做的容错
            self.create_page(page_num)

        return self.__get_page(page_num)

    def get_page_data(self, page_num):
        """
        获取指定页数据
        :param page_num: 页号
        :return:
        """
        page = self.__get_page(page_num)  # 获取页对象
        return page.get_data()  # 获取页对象下所有字段数据

    def get_data(self):
        """
        获取全部数据
        :return:
        """
        data = {}  # 初始化结果字典
        is_first = True  # 设置首次循环标记
        for page_num in self.__page_nums:
            # 遍历所有页
            tmp = self.get_page_data(page_num)  # 获取本轮数据页的所有数据
            for key in tmp.keys():
                # 首轮循环，为字段创建字典键
                if is_first:
                    data[key] = []
            is_first = False  # 设置标记为否
            for field_name, values in tmp.items():
                # 在结果字典中以字段键值映射添加结果
                data[field_name] += values
        return data

    def __check_page_num(self, page_num):
        """
        检查页是否存在
        :param page_num: 页号
        :return: [True | False]
        """
        page_num = str(page_num)
        if page_num not in self.__page_nums:
            # 若不存在，则返回 False
            return False
        return True

    def __get_page(self, page_num):
        """
        获取页对象
        :param page_num: 页号
        :return:
        """
        if not self.__check_page_num(page_num):
            # 判断页是否存在
            raise Exception(f'page {page_num} is not exists.')

        db_cache = Config().active_cache  # 获取当前数据库缓存

        tb_cache = db_cache.get_node(self.__name).node_obj  # 获取数据表缓存
        page_num = str(page_num)
        if tb_cache.get_node(page_num) is None:
            # 缓存结点不存在，则直接创建缓存
            path = join_path(self.__path, str(page_num))  # 拼接数据页路径
            page_obj = Page(path=path)  # 获取页对象
            tb_cache.add_node(node_name=page_num, node_obj=page_obj)

        page = tb_cache.get_node(page_num).node_obj
        return page

    def __get_index(self, index_name):
        """
        获取索引对象
        :param index_name: 索引名称
        :return:
        """
        if index_name not in self.__index_field.keys():
            # 判断索引是否存在
            raise Exception(f'{index_name} is not exists.')

        db_cache = Config().active_cache
        tb_cache = db_cache.get_node(self.__name).node_obj

        if tb_cache.get_node(index_name) is None:
            # 缓存结点不存在，则直接创建
            index_obj = BPTree(path=self.__path, index_name=index_name)
            tb_cache.add_node(node_name=index_name, node_obj=index_obj)

        index = tb_cache.get_node(index_name).node_obj
        return index

    def get_index_list(self):
        """
        获取当前表索引列表
        :return:
        """
        return list(self.__index_field.keys())

    def __get_field_obj(self, field_name):
        """
        获取字段对象
        :param field_name: 字段名
        :return:
        """
        if field_name not in self.__fields.keys():
            # 判断字段对象是否存在
            raise Exception(f'{field_name} is not exists.')
        return self.__fields[field_name]

    def __get_field_type(self, field_name):
        """
        获取字段类型
        :param field_name: 字段名
        :return:
        """
        field = self.__get_field_obj(field_name)  # 获取数据字段对象
        return field.get_type()

    def __get_field_length(self):
        """
        获取字段当前数据长度
        :return:
        """
        data = self.get_data()  # 获取表所有数据
        key = list(data.keys())[0]  # 取出字段
        length = len(data[key])  # 直接获取首个字段的数据长度
        return length

    def __get_page_num(self, index):
        """
        获取页号及索引
        :param index: 待处理索引位置
        :return:
        """
        index = int(index)  # 将索引转换为 int 格式，防止计算类型出错
        page_size = int(self.page_size)  # 获取数据页大小配置
        page_num = index // page_size  # 计算页号
        index = index % page_size  # 计算页中索引值
        return page_num, index

    def __get_name_tmp(self, **options):
        """
        获取参数中的字段
        :param options: 待解析参数集合
        :return:
        """
        name_tmp = []  # 初始化字段结果列表
        params = options  # 取出参数
        for field_name in params.keys():
            if field_name.strip() not in self.__fields.keys():
                # 判断数据字段是否存在
                raise Exception(f'{field_name} is not exists.')
            name_tmp.append(field_name)

        return name_tmp

    def __parse_conditions(self, **conditions):
        """
        解析条件
        :param conditions: 待解析条件
        :return:
        """
        if 'conditions' in conditions:
            # 取出判断条件
            conditions = conditions['conditions']

        if not conditions:
            # 若不存在条件，则直接返回所有索引
            match_index = range(0, self.__get_field_length())
            res = dict(zip(match_index, match_index))
        else:
            # 获取条件字段
            name_tmp = self.__get_name_tmp(**conditions)

            match_tmp = []  # 索引临时存放列表
            match_index = []  # 满足条件索引列表

            index_list = []  # 存在索引的字段列表
            index_matrix = []  # 二维矩阵存放所有索引字段的内容

            for field_name in name_tmp:
                if field_name in self.__index_field.values():
                    index_list.append(field_name)

            for field_name in index_list:
                # 如果字段存在索引，则在索引中添加相应内容
                index_name = [key for key, value in self.__index_field.items() if value == field_name][0]
                index_obj = self.__get_index(index_name)
                case = conditions[field_name]
                condition = case.condition
                symbol = case.symbol
                tmp_index = []

                field_type = self.__get_field_type(field_name)  # 获取字段类型
                set_type = int if field_type is FieldType.INT else float  # 获取python类型对象

                if symbol == '<=':
                    tmp_index = index_obj.get_range_data(right_key=set_type(condition), right_equal=True)

                elif symbol == '>=':
                    tmp_index = index_obj.get_range_data(left_key=set_type(condition), left_equal=True)

                elif symbol == '=':
                    tmp_index = index_obj.get_data(key=set_type(condition))

                elif symbol == '<':
                    tmp_index = index_obj.get_range_data(right_key=set_type(condition), right_equal=False)

                elif symbol == '>':
                    tmp_index = index_obj.get_range_data(left_key=set_type(condition), left_equal=False)

                elif symbol == 'IN':
                    for key in condition:
                        tmp_index.append(index_obj.get_data(key=set_type(key)))

                elif symbol == 'NOT_IN':
                    res = index_obj.traversal_tree()
                    for key in condition:
                        key = set_type(key)
                        if key in res['keys']:
                            res['values'].pop(res['keys'].index(key))
                            res['keys'].pop(res['keys'].index(key))
                    tmp_index = list(res['values'])

                elif symbol == 'RANGE':
                    tmp_index = index_obj.get_range_data(left_key=set_type(condition[0]), left_equal=True,
                                                         right_key=set_type(condition[1]), right_equal=True)

                if tmp_index is None:
                    # 如果索引匹配结果为 None 则代表条件匹配结果为空，则直接返回空
                    return {}
                elif isinstance(tmp_index, int):
                    tmp_index = [tmp_index]

                index_matrix.append(tmp_index if isinstance(tmp_index, list) else list(tmp_index))

            match_tmp = index_matrix[0] if index_list else []

            is_first = True

            for tmp_index in index_matrix:
                # 提取满足所有条件的索引
                match_tmp = list(set(match_tmp) & set(tmp_index))

            if len(name_tmp) == len(index_list):
                # 若匹配条件仅有索引，则直接获取结果，不再执行后续筛选
                match_index = match_tmp

            for field_name in name_tmp:
                if field_name in index_list:
                    # 跳过索引字段
                    continue

                data = {}

                # 获取数据类型
                data_type = self.__get_field_type(field_name)
                if not index_list:
                    # 获取所有数据
                    data_list = self.get_data()[field_name]
                    pk_list = self.get_data()[self.get_primary_key()]
                    data = dict(zip(pk_list, data_list))

                else:
                    for index in match_tmp:
                        page_num, page_index = self.__get_page_num(index)
                        page_index = self.get_real_index([index])[0]
                        page = self.__get_page(page_num)
                        data[index] = page.get_field_data(field_name, page_index)

                # 提取判断条件类
                case = conditions[field_name]

                if not isinstance(case, BaseCase):
                    raise Exception('Condition type error.')

                if is_first:
                    # 首次循环直接获取所有满足条件的索引

                    for index in data.keys():
                        if case(data[index], data_type):
                            match_tmp.append(index)
                            match_index.append(index)
                    is_first = False
                    continue

                for index in match_tmp:
                    # 遍历所有条件，删除不满足条件的索引
                    if not case(data[index], data_type):
                        match_index.remove(index)
                match_tmp = match_index

            res = self.get_real_index(match_index)  # 替换真实索引

        return res

    def get_real_index(self, index_list):
        """
        获取字段真实索引
        :param index_list: 待查找索引列表
        :return:
        """
        pk = self.get_primary_key()  # 获取主键
        res = {}
        for index in index_list:
            # 遍历所有的索引，并在主键中获取到真实位置索引
            page_num, page_index = self.__get_page_num(index)
            page = self.__get_page(page_num)
            value = page.get_field_obj(pk).get_real_index(index)
            value = (int(self.page_size) * page_num) + int(value)
            res[value] = index

        return res

    def insert_data(self, **data):
        """
        插入数据
        :param data: 待插入数据
        :return:
        """
        if 'data' in data:
            data = data['data']

        # 获得主键
        primary_key = self.get_primary_key()

        name_tmp = self.__get_name_tmp(**data)  # 获取待添加数据的数据字段

        if primary_key not in name_tmp:
            # 若主键不在待添加数据的数据字段中，则设置值为自增一
            data[primary_key] = self.__rows + 1

        index = data[primary_key]  # 获取主键索引值
        page_num, _ = self.__get_page_num(index)

        if str(page_num) not in self.__page_nums:
            # 若页指定页不存在，则创建页
            self.create_page(page_num)

        page = self.__get_page(page_num)

        for field_name in self.__fields.keys():
            value = None
            if field_name in data.keys():
                # 获取数据字段值
                value = data[field_name]

            value = page.get_field_obj(field_name).check_value(value)

        for field_name in self.__fields.keys():
            value = None
            if field_name in data.keys():
                # 获取数据字段值
                value = data[field_name]

            try:
                # 添加数据
                page.get_field_obj(field_name).add(value)
                if field_name in self.__index_field.values():
                    # 如果字段存在索引，则在索引中添加相应内容
                    index_name = [key for key, value in self.__index_field.items() if value == field_name][0]
                    index_obj = self.__get_index(index_name)
                    index_obj.insert_item(value, index)
            except Exception as e:
                print(str(e))

        page.increment_length()
        self.__rows += 1  # 数据长度自增

    def search_data(self, fields='*', sort='ASC', **conditions):
        """
        查询数据
        :param fields: 要查询的字段
        :param sort: 排序方式 [ASC | DESC]
        :param conditions: 查询条件
        :return:
        """
        if fields == '*':
            # 如果查询字段为 '*'，则表示查询所有字段
            fields = self.__fields.keys()
        else:
            for field in fields:
                # 遍历判断字段是否存在
                if field not in self.__fields.keys():
                    raise Exception(f'{field} is not exists.')

        res = []  # 初始化结果列表

        match_index = list(self.__parse_conditions(**conditions).keys())  # 解析条件

        match_index.sort()

        for index in match_index:
            # 遍历符合条件的索引，获取数据
            row = {}  # 初始化单行数据结果字典
            page_num, index = self.__get_page_num(index)  # 获取目标页及页内数据索引
            page = self.__get_page(page_num)

            for field_name in fields:
                # 依据字段名，分别获取数据
                row[field_name] = page.get_field_data(field_name, index)
            res.append(row)

        if sort == 'DESC':
            # 排序方法为倒序，取反
            res = res[::-1]

        return res

    def delete_data(self, **conditions):
        """
        删除数据
        :param conditions: 删除条件
        :return:
        """
        match_index = list(self.__parse_conditions(**conditions).keys())  # 解析条件

        for field_name in self.__fields.keys():
            # 遍历字段，进行删除
            count = 0  # 初始化索引偏移量
            match_index.sort()  # 对已匹配索引排序
            tmp_index = match_index[0]  # 以第一个索引为起点，方便后续计算索引偏移量

            for index in match_index:

                if index > tmp_index:
                    # 补偿索引偏移
                    index = index - count

                page_num, index = self.__get_page_num(index)  # 获取目标页及页内数据索引

                page = self.__get_page(page_num)
                field = page.get_field_obj(field_name)
                value = field.get_data(index)
                field.delete(index)  # 删除数据

                if field_name in self.__index_field.values():
                    # 如果字段存在索引，则删除索引内的相关内容
                    index_name = [key for key, value in self.__index_field.items() if value == field_name][0]
                    index_obj = self.__get_index(index_name)
                    index_obj.delete_item(index_obj.root, value)

                count += 1  # 索引偏移自增

    def update_data(self, data, **conditions):
        """
        更新数据
        :param data: 待更新数据
        :param conditions: 更新条件
        :return:
        """
        res = self.__parse_conditions(**conditions)  # 解析条件

        match_index = list(res.keys())

        name_tmp = self.__get_name_tmp(**data)  # 获取待添加数据的数据字段

        for field_name in name_tmp:
            # 遍历待更新字段
            for index in match_index:
                # 遍历匹配索引
                pk = index

                page_num, index = self.__get_page_num(index)  # 获取目标页及页内数据索引
                page = self.__get_page(page_num)

                field = page.get_field_obj(field_name)
                old_value = field.get_data(index)
                field.modify(index, data[field_name])  # 更新数据

                if field_name in self.__index_field.values():
                    # 如果字段存在索引，则修改索引内键的内容
                    index_name = [key for key, value in self.__index_field.items() if value == field_name][0]
                    index_obj = self.__get_index(index_name)
                    index_obj.update_key(old_value, data[field_name])

                if field_name == self.get_primary_key():
                    # 如果字段存在索引，则修改索引内指向的卫星数据内容
                    for index_name in self.__index_field.keys():
                        index_obj = self.__get_index(index_name)
                        key = index_obj.get_key(res[pk])
                        index_obj.update_item(key, data[field_name])

    def commit(self):
        """
        提交表对象
        """
        self.__dump_table()

    def rollback(self):
        """
        回滚表对象
        """
        self.__load_table()

    def __dump_table(self):
        """
        保存表对象
        :return:
        """
        path = join_path(self.__path, self.__name) + '.obj'  # 构造表对象存储路径
        dump_obj(path, self)

    def __load_table(self):
        """
        加载表对象
        :return:
        """
        path = join_path(self.__path, self.__name) + '.obj'  # 构造表对象存储路径
        obj = load_obj(path)  # 获取表对象
        self.__dict__ = obj.__dict__  # 映射对象值
