import os
import prettytable

from syldb.parser import SQLParser
from syldb.handle.configHandle import ConfigHandle
from syldb.conf import Config
from syldb.core.database import Database
from syldb.tools.fileTools import join_path, get_all_subobject, remove_dir
from syldb.core.record import Record
from syldb.handle.queueHandle import OneWayQueue
from syldb.handle.threadHandle import TransactionWorker
from syldb.handle.cacheHandle import CachePool, BranchNode


class Engine:
    """
    数据库引擎对象
    """

    def __init__(self, db_name=None):
        """
        初始化数据库引擎对象
        :param db_name: 数据库名称
        """
        self.__current_db = None  # 当前选中数据库
        self.__data_path = Config().data_path
        self.__exit_signal = False  # 系统退出信号

        if db_name:
            # 若有默认数据库，则直接选中它
            self.select_db(db_name)

        # 数据库操作映射表
        self.__action_map = {  
            'insert': self.__insert,
            'update': self.__update,
            'search': self.__search,
            'delete': self.__delete,
            'drop': self.__drop,
            'show': self.__show,
            'use': self.__use,
            'exit': self.__exit,
            'create': self.__create,
            'call': self.__call,
            'transaction': self.__transaction
        }
            
    def __check_database(self, db_name):
        """
        检查数据库是否存在
        :param db_name:
        :return:
        """
        # 通过直接读取数据目前下的文件夹，直接获取所有数据库
        databases = get_all_subobject(self.__data_path, 'dir')
        if not databases or db_name not in databases:
            return False
        return True

    def create_database(self, db_name):
        """
        创建数据库
        :param db_name: 数据库名称
        :return:
        """
        if self.__check_database(db_name):
            raise Exception(f'{db_name} is exists.')

        _ = Database(db_name=db_name, is_new=True)  # 直接实例化一个数据库对象
        print(f'{db_name} has been created')

    def drop_database(self, db_name):
        """
        删除数据库
        :param db_name: 数据库名称
        :return:
        """
        if not self.__check_database(db_name):
            raise Exception(f'{db_name} is not exists.')

        path = join_path(self.__data_path, db_name)  # 构造数据库存储路径
        res = remove_dir(path)  # 删除数据目录下相应数据的整个文件夹

        cache_pool = CachePool()
        delattr(cache_pool, db_name)    # 删除缓存中的结点

        if res:
            print(f'{db_name} has been deleted.')
        else:
            print(f'{db_name} delete fail.Please check the path and try again.')
            
    def create_index(self, index_name, index_table, index_field):
        """
        创建索引
        :param index_name: 索引名称
        :param index_table: 索引目标表
        :param index_field: 索引字段
        :return:
        """
        self.__check_is_choose()
        table = self.__current_db.get_table_obj(index_table)
        table.create_index(index_name, index_field)
        print(f'{index_name} has been created.')

    def get_table_index(self, table_name):
        """
        获取指定表下的索引
        :param table_name: 数据表名称
        :return:
        """
        self.__check_is_choose()
        table = self.__current_db.get_table_obj(table_name)
        index_list = table.get_index_list()
        res = []
        for index_name in index_list:
            res.append({'index_name': index_name})
        return res

    def drop_table_index(self, table_name, index_name):
        """
        删除指定表下的索引
        :param table_name: 数据表名称
        :param index_name: 索引名称
        :return:
        """
        self.__check_is_choose()
        table = self.__current_db.get_table_obj(table_name)
        table.drop_index(index_name)
        print(f'{index_name} has been deleted.')
        
    def __check_is_choose(self):
        """
        检查是否有数据库被选中
        :return:
        """
        if not self.__current_db:
            # 验证是否有选中数据库，若无选中直接抛出异常，不再进行后续操作
            raise Exception(f'No database is selected.')

    def get_current_db(self):
        """
        获取当前选中数据库
        :return:
        """
        self.__check_is_choose()
        return self.__current_db

    def select_db(self, db_name):
        """
        选中数据库
        :param db_name: 数据库名称
        :return:
        """
        if not self.__check_database(db_name):
            raise Exception(f'{db_name} is not exists.')

        cache_pool = CachePool()

        if cache_pool.get_cache(db_name) is None:
            db_obj = Database(db_name)
            cache_pool.add_cache(db_name, db_obj)

        node = cache_pool.get_cache(db_name)  # 获取目标数据库的缓存池
        self.__current_db = node.obj  # 设置当前活动数据库对象
        setattr(Config(), 'active_cache', node)  # 修改当前活动缓存结点
        print(f'{db_name} has been selected.')

    def __get_table(self, table_name):
        """
        获取数据表对象
        :param table_name: 数据表名称
        :return:
        """
        self.__check_is_choose()

        table = self.__current_db.get_table_obj(table_name)     # 获取从磁盘中加载出的表对象
        return table

    def get_databases(self):
        """
        查询所有数据库
        :return:
        """
        # 获取数据目录下所有文件夹，即为所有数据库
        databases = get_all_subobject(self.__data_path, 'dir')
        res = []
        for database in databases:
            res.append({'database_name': database})
        return res

    def get_tables(self):
        """
        获取当前数据库下所有数据表
        :return:
        """
        self.__check_is_choose()
        tables = self.__current_db.get_all_table()
        res = []
        for table in tables:
            res.append({'table_name': table})
        return res

    def create_table(self, table_name, **options):
        """
        创建数据表
        :param table_name: 数据表名称
        :param options: 数据表字段等信息
        :return:
        """
        self.__check_is_choose()
        self.__current_db.create_table(table_name, **options)
        print(f'{table_name} has been created.')

    def drop_table(self, table_name):
        """
        删除数据表
        :param table_name: 数据表名称
        :return:
        """
        self.__check_is_choose()
        self.__current_db.drop_table(table_name)
        print(f'{table_name} has been deleted.')
        
    def create_procedure(self, procedure_name, procedure_content):
        """
        创建存储过程
        :param procedure_name: 存储过程名称
        :param procedure_content: 存储过程内容
        :return:
        """
        self.__check_is_choose()
        db_name = self.__current_db.get_name()
        record = Record(db_name)  # 获取数据库记录对象
        record.create_procedure(procedure_name, procedure_content)  # 创建存储过程
        print(f'{procedure_name} has been created.')
        
    def get_procedures(self):
        """
        获取当前数据库所有存储过程
        :return:
        """
        self.__check_is_choose()
        db_name = self.__current_db.get_name()
        record = Record(db_name)
        procedure_list = record.get_procedure()
        res = []
        for procedure in procedure_list:
            res.append({'procedure_name': procedure})
        return res

    def drop_procedure(self, procedure_name):
        """
        删除存储过程
        :param procedure_name: 存储过程名称
        :return:
        """
        self.__check_is_choose()
        db_name = self.__current_db.get_name()
        record = Record(db_name)  # 获取数据库记录对象
        record.delete_procedure(procedure_name)  # 删除存储过程
        print(f'{procedure_name} has been deleted.')

    def call_procedure(self, procedure_name, variables):
        """
        调用存储过程
        :param procedure_name: 存储过程名称
        :param variables: 存储过程参数
        :return:
        """
        self.__check_is_choose()
        db_name = self.__current_db.get_name()
        record = Record(db_name)
        procedure = record.get_procedure(procedure_name)  # 获取目标存储过程
        actual_variables = variables.split(',')  # 提取实际参数
        statements = procedure['statement'].split(';')  # 提取语句并分割
        formal_variables = procedure['variables']  # 提取形式参数

        if len(formal_variables) != len(actual_variables):
            # 形参与实参数量不一致
            raise Exception(f'Call {procedure_name} error.')

        for statement in statements[:-1]:
            # 循环执行语句
            final_statement = []
            tmp = statement.split()  # 拆分语句
            for field in tmp:
                for formal_variable in formal_variables:
                    # 遍历参数
                    variable_name = formal_variable['variable_name']
                    variable_index = formal_variable['variable_index']

                    if variable_name in field:
                        # 若语句内包含参数
                        if '(' in field and field.split('(')[1].replace(',', '') == variable_name:
                            # 提出左括号干扰因素
                            field = field.replace(variable_name, actual_variables[variable_index].strip())

                        if ')' in field and field.split(')')[0].strip() == variable_name:
                            # 剔除右括号干扰因素
                            field = field.replace(variable_name, actual_variables[variable_index].strip())

                        if field == variable_name:
                            field = actual_variables[variable_index].strip()

                final_statement.append(field)  # 重新拼接替换参数后语句
            self.execute(' '.join(final_statement))  # 执行语句

    def insert(self, table_name, **data):
        """
        插入数据到指定数据表
        :param table_name: 数据表名称
        :param data: 待插入数据
        :return:
        """
        return self.__get_table(table_name).insert_data(**data)

    def update(self, table_name, data, **conditions):
        """
        更新数据到指定数据表
        :param table_name: 数据标名称
        :param data: 待更新数据
        :param conditions: 更新条件
        :return:
        """
        self.__get_table(table_name).update_data(data, **conditions)

    def delete(self, table_name, **conditions):
        """
        删除数据表内指定数据
        :param table_name: 数据表名称
        :param conditions: 删除条件
        :return:
        """
        return self.__get_table(table_name).delete_data(**conditions)

    def search(self, table_name, fields='*', sort='ASC', **conditions):
        """
        查询指定数据
        :param table_name: 数据表名称
        :param fields: 要查询的字段
        :param sort: 排序方式
        :param conditions: 查询条件
        :return:
        """
        return self.__get_table(table_name).search_data(fields=fields, sort=sort, **conditions)        

    def __insert(self, action):
        """
        插入数据逻辑处理方法
        :param action: 操作内容字典
        :return:
        """
        table_name = action['table']
        data = action['data']

        return self.insert(table_name=table_name, data=data)

    def __update(self, action):
        """
        修改数据逻辑处理方法
        :param action: 操作内容字典
        :return:
        """
        table_name = action['table']
        data = action['data']
        conditions = action['conditions']

        return self.update(table_name=table_name, data=data, conditions=conditions)

    def __delete(self, action):
        """
        删除数据逻辑处理方法
        :param action: 操作内容字典
        :return:
        """
        table_name = action['table']
        conditions = action['conditions']

        return self.delete(table_name=table_name, conditions=conditions)

    def __search(self, action):
        """
        查询数据逻辑处理方法
        :param action: 操作内容字典
        :return:
        """
        table_name = action['table']
        fields = action['fields']
        conditions = action['conditions']

        return self.search(table_name=table_name, fields=fields, conditions=conditions)

    def __drop(self, action):
        """
        删除数据表或数据库逻辑处理方法
        :param action: 操作内容字典
        :return:
        """
        if action['target'] == 'database':
            # 删除数据库
            return self.drop_database(action['name'])

        self.__check_is_choose()

        if action['target'] == 'table':
            # 删除数据表
            return self.drop_table(action['name'])

        elif action['target'] == 'procedure':
            # 删除存储过程
            return self.drop_procedure(action['name'])

        elif action['target'] == 'index':
            # 删除索引
            return self.drop_table_index(table_name=action['table'], index_name=action['name'])

        else:
            # 删除目标非法
            raise Exception(f'{action["target"]} is illegal.')

    def __show(self, action):
        """
        查询数据库或数据表逻辑处理方法
        :param action: 操作内容字典
        :return:
        """
        if action['target'] == 'databases':
            return self.get_databases()

        elif action['target'] == 'tables':
            return self.get_tables()

        elif action['target'] == 'procedure':
            return self.get_procedures()

        elif action['target'] == 'index':
            return self.get_table_index(action['table'])

    def __use(self, action):
        """
        选中数据库逻辑处理方法
        :param action: 操作内容字典
        :return:
        """
        return self.select_db(action['database'])

    @staticmethod
    def __exit(*args):
        return 'exit'

    def __create(self, action):
        """
        创建数据表或数据库语句
        :param action: 操作内容字典
        :return:
        """
        target = action['target']
        name = action['name']
        options = action['options']

        if target.upper() == 'TABLE':
            # 创建数据表
            self.create_table(table_name=name, options=options)

        elif target.upper() == 'DATABASE':
            # 创建数据库
            self.create_database(db_name=name)

        elif target.upper() == 'PROCEDURE':
            # 创建存储过程
            self.create_procedure(procedure_name=name, procedure_content=options)

        elif target.upper() == 'INDEX':
            # 创建索引
            self.create_index(index_name=name, index_table=options['table'], index_field=options['field'])

        else:
            # 创建目标非法
            raise Exception(f'{target} is illegal.')

    def __call(self, action):
        """
        调用存储过程
        :param action: 操作内容字典
        :return:
        """
        procedure_name = action['name']
        variables = action['variables']
        self.call_procedure(procedure_name, variables)

    def __execute_transaction_statement(self, statement):
        """
        执行事务子语句
        :param statement: 待执行语句
        :return:
        """
        while True:
            try:
                res = self.execute(statement)
                self.display(res)
                return True
            except Exception as e:
                print(f'{statement} execute fail.{str(e)}')
                return statement

    def __transaction(self, action):
        """
        事务操作
        :param action: 操作内容字典
        :return:
        """
        self.commit()  # 执行事务前先提交当前数据的操作
        statements = action['statements']
        over_signal = False  # 初始化事务退出标识
        commit_signal = True
        error_statement = ''  # 初始化错误语句
        setattr(Config(), 'auto_commit_signal', False)  # 修改自动提交标识为否
        in_queue = OneWayQueue()  # 入队列
        out_queue = OneWayQueue()  # 出队列

        # 创建事务执行线程
        thread = TransactionWorker(self.__execute_transaction_statement, in_queue, out_queue)
        thread.start()
        for statement in statements:
            # 遍历事务子语句
            if statement.strip().upper() in ['COMMIT', 'END']:
                # 事务执行完毕，提交
                in_queue.close()
                break
            elif statement.strip().upper() == 'ROLLBACK':
                # 事务回滚
                in_queue.close()
                commit_signal = False
                break
            elif statement == '':
                # 跳过空行
                continue
            else:
                # 放入子语句
                in_queue.put(statement.strip())
        in_queue.close()
        thread.join()  # 挂起线程

        for _ in range(out_queue.qsize()):
            # 遍历执行结果
            item = out_queue.get()
            if item is not True:
                # 执行错误，则提取错误语句，并做回滚标识
                over_signal = False
                error_statement = item
                break
            continue
        else:
            # 子语句全部正确执行，做提交标识
            over_signal = True

        if over_signal and commit_signal:
            self.commit()
        else:
            print(f'{error_statement} execute fail.Transaction has been rollback.')
            self.rollback()

        setattr(Config(), 'auto_commit_signal', True)  # 修改自动提交标识为是
        setattr(Config(), 'transaction_signal', False)
        thread._stop()

    @staticmethod
    def commit():
        """
        提交
        :return:
        """
        node = Config().active_cache
        if node is not None:
            node.commit()

    @staticmethod
    def rollback():
        """
        回滚
        :return:
        """
        node = Config().active_cache
        node.rollback()

    def execute(self, statement):
        """
        sql 语句执行方法
        :param statement: 待执行语句
        :return:
        """
        action = SQLParser().parse(statement)

        res = None

        if action['type'] in self.__action_map:
            res = self.__action_map.get(action['type'])(action)

        return res

    def display(self, res):
        """
        sql 语句执行结果展示方法
        :param res: 执行结果
        :return:
        """
        if isinstance(res, str) and res.upper() == 'EXIT':
            print('Goodbye!')
            self.__exit_signal = True
            return

        try:
            if res:
                pt = prettytable.PrettyTable(res[0].keys())
                pt.align = 'l'
                for line in res:
                    pt.align = 'r'
                    pt.add_row(line.values())
                print(pt)
                return
        except Exception as e:
            print(f'Display error.{str(e)}')
            return

    def run(self):
        """
        数据库引擎，交互界面启动方法
        :return:
        """

        content = ''  # 初始化用户输入内容
        over_flag = ';'  # 定义语句结束标识符
        while True:
            # loop
            statement = input('isadb>')
            if statement == '':
                # 防止连续回车
                continue

            content += statement.strip()  # 拼接用户输入语句

            if content.split(' ')[0].upper() == 'DELIMITER':
                # 直接处理修改结束标识符
                over_flag = content.split(' ')[1]
                print(over_flag)
                content = ''
                continue

            if content.split(over_flag)[0].upper() in ['BEGIN', 'START TRANSACTION']:
                setattr(Config(), 'transaction_signal', True)
                if 'ROLLBACK' in content.upper():
                    content = ''
                    print(f'Transaction is rollback')
                    setattr(Config(), 'transaction_signal', False)
                    continue
                if 'COMMIT' not in content.upper() and 'END' not in content.upper():
                    continue

            if content[-len(over_flag):] != over_flag:
                # 结束标志判断，若未结束，则继续接收语句，允许用户换行的友好操作
                continue

            try:
                # 提取语句，去除结束标识符
                statement = content.split(over_flag)[0]

                if getattr(Config(), 'transaction_signal', False) and content.split(over_flag)[0].upper() in ['BEGIN', 'START TRANSACTION']:
                    statement = content
                res = self.execute(statement)  # 执行用户输入语句，取得执行结果
                content = ''  # 清空语句
                self.display(res)  # 展示执行结果到用户交互界面

                if self.__exit_signal:
                    # 退出信号为真，退出用户交互
                    # 将所有修改保存到磁盘
                    CachePool().flush_cache_to_disk()
                    return

            except Exception as e:
                print(f'System has been error.{str(e)}')
                content = ''

def init():
    # 构造默认配置文件路径
    path = join_path(os.getcwd(), 'syldb', 'conf')

    # 实例化配置文件操作对象
    _ = ConfigHandle(path, file_name='syldb.ini')

    setattr(Config(), 'auto_commit_signal', True)  # 初始化自动提交信号
    setattr(Config(), 'active_cache', None)  # 初始化活动缓存结点
    setattr(Config(), 'transaction_signal', False)
    _ = CachePool()  # 实例化缓存池


if __name__ != '__main__':
    # 执行初始化操作
    init()