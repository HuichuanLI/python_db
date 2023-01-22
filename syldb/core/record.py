from syldb.tools.fileTools import is_exists, join_path
from syldb.conf import Config
from syldb.core.field import Field
from syldb.tools.storageTools import dump_obj, load_obj


class Record:
    """
    数据库记录对象
    """

    def __init__(self, db_name):
        """
        初始化数据库记录对象
        :param db_name:
        """
        self.path = join_path(Config().work_path, Config().data_path, db_name)      # 数据库记录保存路径
        self.db_name = db_name  # 数据库名称
        self.proc = {}          # 存储过程记录
        self.table_fields = {}  # 数据表字段记录

        if not is_exists(join_path(self.path, self.db_name) + '.rcd'):
            # 若数据库记录对象不存在，直接创建
            self.__dump_rcd()

        self.__load_rcd()   # 加载数据库记录对象

    def get_table_field(self, table_name):
        """
        获取数据表字段
        :param table_name: 数据表名称
        :return:
        """
        if table_name not in self.table_fields.keys():
            raise Exception(f'{table_name} is not have field record.')
        return self.table_fields[table_name]

    def add_table_field(self, table_name, field_objs):
        """
        添加数据表字段记录
        :param table_name: 数据表名称
        :param field_objs: 数据表字段
        :return:
        """
        if 'field_objs' in field_objs:
            # 提取数据表字段
            field_objs = field_objs['field_objs']

        for field_obj in field_objs.values():
            # 判断数据表字段是否为字段对象
            if not isinstance(field_obj, Field):
                raise Exception(f'{table_name} field is except')

        self.table_fields[table_name] = field_objs  # 添加数据表字段记录
        self.__dump_rcd()   # 保存数据库记录

    def delete_table_field(self, table_name):
        """
        删除数据表字段记录
        :param table_name: 数据表名称
        :return:
        """
        self.table_fields.pop(table_name, True)
        self.__dump_rcd()
        
    def create_procedure(self, procedure_name, procedure_content):
        """
        创建存储过程记录
        :param procedure_name: 存储过程名称
        :param procedure_content: 存储过程内容
        :return:
        """
        if procedure_name in self.proc.keys():
            # 存储过程已存在
            raise Exception(f'{procedure_name} is exist.')

        self.proc[procedure_name] = procedure_content   # 保存存储过程内容
        self.__dump_rcd()

    def get_procedure(self, procedure_name=None):
        """
        获取存储过程记录
        :param procedure_name: 存储过程名称
        :return:
        """
        if procedure_name is not None:
            # 传入存储过程名称，获取单个存储过程记录
            if procedure_name not in self.proc.keys():
                # 存储过程不存在
                raise Exception(f'{procedure_name} is not exist.')
            return self.proc[procedure_name]
        else:
            # 获取当前所有存储过程记录
            return list(self.proc.keys())

    def delete_procedure(self, procedure_name):
        """
        删除存储过程记录
        :param procedure_name: 存储过程名称
        :return:
        """
        if procedure_name not in self.proc.keys():
            # 存储过程不存在
            raise Exception(f'{procedure_name} is not exist.')

        del self.proc[procedure_name]   # 删除记录
        self.__dump_rcd()
        
    def __dump_rcd(self):
        """保存数据库记录对象"""
        path = join_path(self.path, self.db_name) + '.rcd'
        dump_obj(path, self)

    def __load_rcd(self):
        """加载数据库记录对象"""
        path = join_path(self.path, self.db_name) + '.rcd'
        obj = load_obj(path)
        self.__dict__ = obj.__dict__