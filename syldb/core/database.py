from syldb.conf import Config
from syldb.tools.fileTools import join_path, is_exists, mkdir, remove_dir
from syldb.core.record import Record
from syldb.core.table import Table
from syldb.tools.storageTools import dump_obj, load_obj
from syldb.handle.cacheHandle import BranchNode


class Database:
    """
    数据库对象
    """

    def __init__(self, db_name, is_new=False):
        """
        初始化数据库对象
        :param db_name: 数据库名称
        :param is_new: 是否新建数据库
        """
        self.__name = db_name     # 数据库名
        self.__path = join_path(Config().work_path, Config().data_path, db_name)  # 数据库保存路径
        self.__table_names = []   # 数据表名称

        if is_new and not is_exists(self.__path):
            """
            新建数据库
            """
            self.__path = mkdir(self.__path)    # 创建数据库存储路径
            _ = Record(db_name=self.__name)   # 创建记录对象
            self.__dump_database()          # 保存数据库

        self.__load_database()              # 加载数据库
        
    def create_table(self, table_name, **options):
        """
        创建数据表
        :param table_name: 数据表名称
        :param options: 数据表字段
        :return:
        """
        if self.__check_table_name(table_name):
            # 数据表唯一，数据表存在则抛出异常
            raise Exception(f'{table_name} is exists.')

        if 'options' in options:
            # 提取数据表字段
            options = options['options']

        if not options:
            # 数据表必须存在字段，若不存在直接抛出异常
            raise Exception(f'{table_name} do not have field.')

        try:
            rcd = Record(self.__name)     # 获取数据库记录对象
            rcd.add_table_field(table_name, options)    # 添加数据表字段记录

            _ = Table(db_name=self.__name, tb_name=table_name, is_new=True)   # 创建数据表
            self.__table_names.append(table_name)     # 保存数据表名称
            self.__dump_database()                  # 保存数据库

        except Exception as e:
            print(str(e))

    def drop_table(self, table_name):
        """
        删除数据表
        :param table_name: 数据表名称
        :return:
        """
        if not self.__check_table_name(table_name):
            # 验证数据表是否存在
            raise Exception(f'{table_name} is not exists.')

        try:
            path = join_path(self.__path, table_name)  # 构造数据表保存路径
            remove_dir(path)  # 删除整个数据表文件夹
            self.__table_names.remove(table_name)  # 删除数据表名称记录
            rcd = Record(self.__name)
            rcd.delete_table_field(table_name)  # 删除数据表字段记录
            db_cache = getattr(Config(), 'active_cache')
            if getattr(db_cache, table_name, False):
                delattr(db_cache, table_name)  # 删除缓存中的结点
            self.__dump_database()
        except Exception as e:
            print(str(e))

    def __check_table_name(self, table_name):
        """
        检查数据表是否存在
        :param table_name: 数据表名称
        :return:
        """
        if table_name not in self.__table_names:
            return False
        return True
        
    def get_table_obj(self, table_name):
        """
        获取数据表对象
        :param table_name: 数据表名称
        :return:
        """
        if not self.__check_table_name(table_name):
            # 验证数据表是否存在
            raise Exception(f'{table_name} is not exists.')

        db_cache = getattr(Config(), 'active_cache')

        if db_cache.get_node(table_name) is None:
            # 数据表缓存不存在，则直接创建
            tb_obj = Table(db_name=self.__name, tb_name=table_name)
            tb_node = BranchNode(node_name=table_name, obj=tb_obj)
            db_cache.add_node(node_name=table_name, node_obj=tb_node)

        tb_cache = db_cache.get_node(table_name).node_obj  # 从缓存中获取数据表缓存

        return tb_cache.obj  # 返回数据表对象

    def get_all_table(self):
        """
        获取数据库包含的所有数据表
        :return:
        """
        return self.__table_names

    def get_name(self):
        """
        获取数据库名称
        :return:
        """
        return self.__name

    def commit(self):
        """
        提交数据库操作
        :return:
        """
        self.__dump_database()

    def rollback(self):
        """
        回滚数据库操作
        :return:
        """
        self.__load_database()
        
    def __dump_database(self):
        """保存库对象"""
        # 构造数据库对象保存路径
        path = join_path(self.__path, self.__name) + '.obj'
        dump_obj(path, self)    # 保存数据库对象

    def __load_database(self):
        """加载库对象"""
        # 构造数据库对象保存路径
        path = join_path(self.__path, self.__name) + '.obj'
        obj = load_obj(path)    # 加载数据库对象
        self.__dict__ = obj.__dict__