from core import *
from core.database import Database
from core import SerializedInterface
import os
import base64

from core.database import Database


# 解码数据
def _decode_db(content):
    content = base64.decodebytes(content)
    return content.decode()[::-1]


# 编码数据
def _encode_db(content):
    content = content[::-1].encode()
    return base64.encodebytes(content)


# 数据库引擎
class Engine:
    def __init__(self, db_name=None, format_type='dict', path='db.data'):
        self.__database_objs = {}  # 数据库映射表
        self.__database_names = []  # 数据库名字集合
        self.__current_db = None  # 标示当前使用的数据库
        self.path = path  # 数据库存放路径名
        self.__format_type = format_type  # 数据默认返回格式

        # 如果初始化时数据库名字参数不为空，调用 select_db 方法选中数据库
        if db_name is not None:
            self.select_db(db_name)

    # 创建数据库
    def create_database(self, database_name):
        # 判断数据库名字是否存在，如果存在，抛出数据库已存在异常
        if database_name in self.__database_objs:
            raise Exception('Database exist')

        # 追加数据库名字
        self.__database_names.append(database_name)

        # 关联数据库对象和数据库名
        self.__database_objs[database_name] = Database(database_name)

    # 删除数据库
    def drop_database(self, database_name):
        # 如果数据库名字不存在，则抛出数据库不存在异常
        if database_name not in self.__database_objs:
            raise Exception('Database not exists')

        # 从数据库名字集合中移除
        self.__database_names.remove(database_name)

        # 移除数据库名和对象的映射
        self.__database_objs.pop(database_name, True)

    # 选择数据库
    def select_db(self, db_name):
        # 如果不存在该数据库索引，抛出数据库不存在异常
        if db_name not in self.__database_objs:
            raise Exception('has not this database')

        # 将对应名字的 Database 对象赋值给 __current_db
        self.__current_db = self.__database_objs[db_name]

    # 序列化数据库
    def serialized(self):
        return SerializedInterface.json.dumps([
            database.serialized() for database in self.__database_objs.values()
        ])

    # 提交数据库改动
    def commit(self):
        self.__dump_databases()

    # 回滚数据库改动
    def rollback(self):
        self.__load_databases()

    # 保存数据库
    def __dump_databases(self):
        with open(self.path, 'wb') as f:
            # 编码 Json 字符串
            content = _encode_db(self.serialized())

            # 保存数据到本地
            f.write(content)

    # 反序列化数据库
    def deserialized(self, content):
        # 解析 Json 数据
        data = SerializedInterface.json.loads(content)

        # 因为每一条就是一个 Database 对象的 Json 数据，所以直接遍历再调用 Database 的反序列化方法就行了
        for obj in data:
            # 实例化 Database 对象
            database = Database.deserialized(obj)

            # 获取数据库名字
            db_name = database.get_name()

            # 追加数据库名字和绑定数据库对象
            self.__database_names.append(db_name)
            self.__database_objs[db_name] = database

        # 加载数据库

    def __load_databases(self):
        # 如果数据文件不存在，则直接退出
        if not os.path.exists(self.path):
            return

        # 读取文件数据
        with open(self.path, 'rb') as f:
            content = f.read()

        # 如果数据不为空
        if content:
            # 解码数据，并把数据传给反序列化函数
            self.deserialized(_decode_db(content))

    # 查询指定数据表数据
    def search(self, table_name, fields='*', sort='ASC', **conditions):
        # 通过数据表名字获取指定的 Table 对象，再调用它的 search 方法获取查询结果
        return self.__get_table(table_name).search(fields=fields, sort=sort, format_type=self.__format_type,
                                                   **conditions)

    # 获取数据表
    def __get_table(self, table_name):

        # 判断当前是否有选中的数据库
        self.__check_is_choose()

        # 获取对应的 Table 对象
        table = self.__current_db.get_table_obj(table_name)

        # 如果 Table 对象为空，抛出异常
        if table is None:
            raise Exception('not table %s' % table_name)

        # 返回 Table 对象
        return table

        # 检查是否选择数据库

    def __check_is_choose(self):
        # 如果当前没有选中的数据库，抛出为选择数据库异常
        if not self.__current_db or not isinstance(self.__current_db, Database):
            raise Exception('No database choose')
        # 插入数据到指定数据表

    def insert(self, table_name, **data):
        return self.__get_table(table_name).insert(**data)

    # 更新指定数据表数据
    def update(self, table_name, data, **conditions):
        self.__get_table(table_name).update(data, **conditions)

    # 删除指定数据表数据
    def delete(self, table_name, **conditions):
        return self.__get_table(table_name).delete(**conditions)

    def create_table(self, name, **options):
        self.__check_is_choose()
        self.__current_db.create_table(name, **options)

    # 获取数据库名
    def get_database(self, format_type='list'):
        databases = self.__database_names

        if format_type == 'dict':
            tmp = []
            for database in databases:
                tmp.append({'name': database})

            databases = tmp

        return databases

    # 获取数据表
    def get_table(self, format_type='list'):
        self.__check_is_choose()

        tables = self.__current_db.get_table()

        if format_type == 'dict':
            tmp = []
            for table in tables:
                tmp.append({'name': table})

            tables = tmp

        return tables

