import re

from syldb.case import *
from syldb.core import FieldKey, FieldType
from syldb.core.field import Field
from syldb.conf import Config


class SQLParser:
    """
    语法解析对象
    """

    def __init__(self):
        """
        初始化语法解析对象
        """

        # 操作关键字与解析方法映射
        self.__action_map = {
            'SELECT': self.__select,
            'UPDATE': self.__update,
            'DELETE': self.__delete,
            'INSERT': self.__insert,
            'CREATE': self.__create,
            'USE': self.__use,
            'EXIT': self.__exit,
            'QUIT': self.__exit,
            'SHOW': self.__show,
            'DROP': self.__drop,
            'CALL': self.__call,
            'START': self.__start,
            'BEGIN': self.__start
        }

        self.__symbol_map = {
            'IN': InCase,
            'NOT_IN': NotInCase,
            '>': GreaterCase,
            '<': LessCase,
            '=': IsCase,
            '!=': IsNotCase,
            '>=': GAECase,
            '<=': LAECase,
            'LIKE': LikeCase,
            'RANGE': RangeCase
        }

        # 操作关键字与正则表达式映射
        self.__pattern_map = {
            'SELECT': r'(SELECT|select) (.*) (FROM|from) (.*)',
            'UPDATE': r'(UPDATE|update) (.*) (SET|set) (.*)',
            'INSERT': r'(INSERT|insert) (INTO|into) (.*)(\s*)\((.*)\) (VALUES|values)(\s*)\((.*)\)',
            'CREATE': r'(CREATE|create) (.*) (.*)\((.*)\)(.*)',
            'PROCEDURE': r'(CREATE|create) (PROCEDURE|procedure) (.*)\((.*)\);\s*(BEGIN|begin);\s*(.*)(END|end)',
            'INDEX': r'(CREATE|create) (INDEX|index) (.*) (ON|on) (.*)\((.*)\)'
        }

        # 字段约束与字段约束枚举类型映射
        self.__key_map = {
            'PRIMARY KEY': FieldKey.PRIMARY,
            'AUTO_INCREMENT': FieldKey.INCREMENT,
            'UNIQUE': FieldKey.UNIQUE,
            'NOT NULL': FieldKey.NOT_NULL,
            'NULL': FieldKey.NULL
        }

        # 数据类型与字段数据类型映射
        self.__type_map = {
            'INT': FieldType.INT,
            'VARCHAR': FieldType.VARCHAR,
            'FLOAT': FieldType.FLOAT,
        }

    @staticmethod
    def __filter_space(statements):
        """
        拆分条件语句
        :param statements: 待拆分语句
        :return:
        """
        ret = []
        for tmp in statements:
            # 遍历所有子语句，去除空格与 and 字段
            if tmp.strip() == '' or tmp.strip() == 'AND':
                continue
            ret.append(tmp)

        return ret

    def parse(self, statement):
        """
        语法解析核心方法
        :param statement: 待解析语句
        :return:
        """
        source_statement = statement  # 保存初始语句

        if 'where' in statement:
            # 以 where 关键字为基准拆分语句
            statement = statement.split('where')
        else:
            statement = statement.split('WHERE')

        # 提取基础语句及空格
        base_statement = self.__filter_space(statement[0].split(' '))

        if getattr(Config(), 'transaction_signal', False) and (
                'BEGIN' in source_statement.upper() or 'START TRANSACTION' in source_statement.upper()):
            # 若当前为事务模式，且为完整事务语句，则匹配完整语句
            base_statement = self.__filter_space(source_statement.split(' '))


        if len(base_statement) < 2 and base_statement[0].upper() not in ['EXIT', 'QUIT']:
            # 语句错误，除退出语句外，所有语句长度均应大于等于2
            raise Exception(f'The {source_statement} is incorrect.')

        action_type = base_statement[0].upper().strip()     # 提取操作关键字

        if action_type not in self.__action_map:
            # 关键字非法
            raise Exception(f'The {source_statement} is illegal and the {action_type} operation is not supported.')

        action = self.__action_map[action_type](base_statement)     # 反射相应操作解析方法，获取解析结果

        if action is None or 'type' not in action:
            # 操作非法，无法解析出相应操作
            raise Exception(f'The {source_statement} is incorrect.')

        action['conditions'] = {}  # 初始化动作字典中的条件映射

        conditions = None

        if len(statement) == 2:
            # 若存在条件，则提取条件并处理空格
            conditions = self.__filter_space(statement[1].split(' '))

        if conditions:
            # 解析条件
            for index in range(0, len(conditions), 4):
                # 三个为一组，解析条件
                field = conditions[index]  # 提取条件字段
                symbol = conditions[index + 1].upper()  # 提取条件关键字
                condition = conditions[index + 2]  # 提取条件

                if symbol == 'RANGE':
                    # 去除 range 条件中的括号
                    condition_tmp = condition.replace(
                        '(', '').replace(')', '').split(',')
                    start = condition_tmp[0]
                    end = condition_tmp[1]
                    case = self.__symbol_map[symbol](start, end)

                elif symbol == 'IN' or symbol == 'NOT_IN':
                    # 去除 in 与 not in 条件中的括号，并转换为列表
                    condition = condition.replace(
                        '(', '').replace(')', '').split(',')
                    case = self.__symbol_map[symbol](condition)

                else:
                    case = self.__symbol_map[symbol](condition)

                action['conditions'][field] = case  # 添加条件映射到动作字典

        return action

    @staticmethod
    def __change_type(value):
        """
        修改值类型
        :param value: 待修改类型值
        :return:
        """
        if "'" in value or '"' in value:
            # 字符串类型，去掉可能存在的引号
            value = value.replace('"', '').replace("'", "").strip()
        elif '.' in value:
            # 尝试转化为浮点类型，不排除输入值异常的可能性
            try:
                value = float(value)
            except ValueError:
                return None
        else:
            # 尝试转化为整数类型，不排除输入值异常的可能性
            try:
                value = int(value)
            except ValueError:
                return None
        return value

    def __get_comp(self, action):
        """
        获取正则表达式
        :param action: 动作关键字
        :return:
        """
        return re.compile(self.__pattern_map[action])

    def __select(self, statement):
        """
        查询语句解析方法
        :param statement: 待解析语句
        :return:
        :example: select * from t_table
        """
        comp = self.__get_comp('SELECT')

        # 匹配查询语句
        res = comp.findall(' '.join(statement))

        if res is not None and len(res[0]) == 4:
            fields = res[0][1]  # 提取字段
            table = res[0][3]  # 提取目标表

            if fields != '*':
                # 若非查询所有字段，则获取查询字段，去除空格防止字段名不匹配
                fields = [field.strip() for field in fields.split(',')]

            return {
                'type': 'search',
                'fields': fields,
                'table': table
            }

        return None

    def __update(self, statement):
        """
        更新语句解析方法
        :param statement: 待解析语句
        :return:
        """

        comp = self.__get_comp('UPDATE')

        # 匹配更新语句
        res = comp.findall(' '.join(statement))

        if res is not None and len(res[0]) == 4:
            data = {
                'type': 'update',
                'table': res[0][1],  # 提取目标表
                'data': {}
            }

            target_items = res[0][3].split(',')  # 提取目标字段

            for item in target_items:
                # 解析所有待修改内容，以 = 分割，提取字段与值
                item = item.split('=')
                field = item[0].strip()

                value = self.__change_type(item[1].strip())  # 修正值类型，防止后续类型错误

                if value is None:
                    # 值异常或为空
                    return None

                data['data'][field] = value
            return data
        return None

    @staticmethod
    def __delete(statement):
        """
        删除语句解析方法
        :param statement: 待解析语句
        :return:
        """
        return {
            'type': 'delete',
            'table': statement[2]  # 提取目标表名称
        }

    def __insert(self, statement):
        """
        插入语句解析方法
        :param statement: 待解析语句
        :return:
        """
        comp = self.__get_comp('INSERT')

        # 解析插入语句
        res = comp.findall(' '.join(statement))

        if res is not None and len(res[0]) == 8:
            data = {
                'type': 'insert',
                'table': res[0][2].strip(),  # 提取目标表
                'data': {}
            }

            fields = res[0][4].split(',')  # 提取所有字段
            values = res[0][7].split(',')  # 提取所有值

            if len(fields) != len(values):
                # 字段与值数量不匹配，视为异常
                return None

            for i in range(len(fields)):
                # 遍历所有字段
                field = fields[i].strip()
                value = self.__change_type(values[i].strip())

                if value is None:
                    # 值异常或为空
                    return None

                data['data'][field] = value  # 映射字段与值
            return data
        return None

    def __create(self, statement):
        """
        创建数据库、表解析方法
        :param statement:
        :return:
        """
        target = statement[1]  # 提取创建对象类型

        if target.upper() == 'DATABASE':
            # 创建数据库
            return {
                'type': 'create',
                'target': 'database',
                'name': statement[2],  # 提取数据库名称
                'options': None
            }

        elif target.upper() == 'TABLE':
            # 创建数据表
            tmp_statement = ' '.join(statement)  # 复制临时操作变量

            tmp_statement = re.sub(r"\(\d+\S*\d*\)", '', tmp_statement)  # 去除字段长度

            # 匹配单独指定方式的字段主键
            pk_comp = re.compile(r',(PRIMARY KEY|primary key)\s*\((\s*)([\w-]*)(\s*)\)')
            pk = pk_comp.findall(tmp_statement)
            primary_key = None
            if pk:
                # 若存在单独指定方式的字段主键，则替换它，保证解析格式正确
                primary_key = pk[0][2].replace('`', '')
                tmp_statement = re.sub(r',(PRIMARY KEY|primary key)\s*\((\s*)([\w-]*)(\s*)\)', '', tmp_statement)

            comp = self.__get_comp('CREATE')  # 获取创建表正则表达式
            res = comp.findall(tmp_statement)  # 匹配创建语句内容

            if res is not None and len(res[0]) == 5:
                # 匹配成功
                data = {
                    'type': 'create',
                    'target': 'table',
                    'name': res[0][2].replace('`', ''),  # 提取数据表名称
                    'options': None
                }

                field_items = res[0][3].split(',')  # 提取数据表内字段语句
                fields = {}
                for field_item in field_items:
                    # 遍历字段语句，创建字段对象
                    field_info_list = field_item.strip().split(' ')  # 拆分字段内容

                    field_name = field_info_list[0].replace('`', '')  # 提取字段名
                    field_type = field_info_list[1]  # 提取字段值类型
                    keys = []
                    if field_name == primary_key:
                        # 若存在单独指定方式的字段主键，则直接添加主键约束
                        keys.append(self.__key_map['PRIMARY KEY'])

                    if not isinstance(self.__type_map[field_type.upper()], FieldType):
                        # 字段值类型非法
                        raise Exception(
                            f'Type {field_type} of the {field_name} field is incorrect.It must be in [int | float | varchar].')
                    data_type = self.__type_map[field_type.upper()]

                    for i in range(2, len(field_info_list), 2):
                        # 解析字段约束，字段允许多个约束
                        field_key = ''
                        if field_info_list[i].upper() == 'PRIMARY' and i < len(field_info_list) - 1:
                            # 解析字段定义时的主键
                            if field_info_list[i + 1].upper() == 'KEY':
                                field_key = 'PRIMARY KEY'

                        elif field_info_list[i].upper() == 'NOT' and i < len(field_info_list) - 1:
                            # 解析非空约束
                            if field_info_list[i + 1].upper() == 'NULL':
                                field_key = 'NOT NULL'

                        elif field_info_list[i].upper() == 'NULL' and field_info_list[i - 1].upper() == 'NOT':
                            # 跳过非空约束末位字段
                            continue

                        elif field_info_list[i].upper() == 'KEY' and field_info_list[i - 1].upper() == 'PRIMARY':
                            # 跳过主键约束末位字段
                            continue

                        else:
                            field_key = field_info_list[i].upper()

                        if field_key not in self.__key_map.keys():
                            # 字段约束类型非法
                            raise Exception(
                                f'Key {field_key} of the {field_name} field is incorrect.It must be in [null | not null | primary key | unique | auto_increment].')

                        keys.append(self.__key_map[field_key])

                    if len(set(keys)) < len(keys):
                        # 重复定义字段约束，视为非法
                        raise Exception(
                            f'Field key of the {field_name} has been conflict.Please check it and try again.')
                    fields[field_name] = Field(data_type=data_type, keys=keys)  # 映射字段名及字段对象
                data['options'] = fields
                return data
        elif target.upper() == 'PROCEDURE':
            # 创建存储过程
            comp = self.__get_comp('PROCEDURE')
            res = comp.findall(' '.join(statement))

            if res is not None and len(res[0]) == 7:
                # 匹配成功
                data = {
                    'type': 'create',
                    'target': 'procedure',
                    'name': res[0][2].replace('`', ''),  # 提取存储过程名称
                    'options': None
                }

                # 初始化存储过程内容映射
                options = {
                    'variables': [],
                    'statement': res[0][5].strip()
                }

                variables = res[0][3].split(',')
                index = 0  # 初始化参数起始索引
                for variable in variables:
                    # 遍历存储过程参数
                    variable_info = variable.strip().split(' ')
                    variable_type = variable_info[0]  # 参数类型
                    variable_name = variable_info[1]  # 参数名
                    variable_value_type = variable_info[2]  # 参数值类型

                    if variable_type.upper() not in ['IN', 'OUT']:
                        # 参数类型非法
                        raise Exception(f'The {variable_name} type is except.It must be in [IN | OUT]')

                    tmp = {
                        'variable_name': variable_name,
                        'variable_type': variable_type,
                        'variable_value_type': variable_value_type,
                        'variable_index': index
                    }
                    options['variables'].append(tmp)
                    index += 1
                data['options'] = options
                return data
                
        elif target.upper() == 'INDEX':
            # 创建索引
            comp = self.__get_comp('INDEX')
            res = comp.findall(' '.join(statement))

            if res is not None and len(res[0]) == 6:
                # 匹配成功
                return {
                    'type': 'create',
                    'target': 'index',
                    'name': res[0][2].strip(),
                    'options': {
                        'table': res[0][4].strip(),
                        'field': res[0][5].strip()
                    }
                }
                
        return None

    @staticmethod
    def __use(statement):
        """
        选择数据库解析方法
        :param statement: 待解析语句
        :return:
        """
        return {
            'type': 'use',
            'database': statement[1]  # 待选中数据库名称
        }

    @staticmethod
    def __exit(*args):
        """
        退出语句解析方法，不需要任何参数，直接退出即可
        :param args: 接受任意参数，不做解析
        :return:
        """
        return {
            'type': 'exit'
        }

    @staticmethod
    def __show(statement):
        """
        数据库、表查询语句解析方法
        :param statement: 待解析语句
        :return:
        """
        target = statement[1].lower()  # 提取展示类型

        if target in ['databases', 'tables', 'procedure']:
            return {
                'type': 'show',
                'target': target
            }
        elif target == 'index':
            return {
                'type': 'show',
                'target': target,
                'table': statement[3].strip()
            }

        return None

    @staticmethod
    def __drop(statement):
        """
        删除数据库、表语句解析方法
        :param statement: 待解析语句
        :return:
        """
        target = statement[1].lower()  # 提取删除类型

        if target in ['database', 'table', 'procedure']:
            return {
                'type': 'drop',
                'target': target,
                'name': statement[2]
            }

        elif target == 'index':
            return {
                'type': 'drop',
                'target': target,
                'name': statement[2].strip(),
                'table': statement[4].strip()
            }

        return None

    @staticmethod
    def __call(statement):
        """
        调用存储过程解析方法
        :param statement: 待解析语句
        :return:
        """
        statement = ' '.join(statement[1:])
        name = statement.split('(')[0]  # 提取存储过程名
        variables = statement.split('(')[1].split(')')[0].strip()  # 提取参数
        return {
            'type': 'call',
            'name': name,
            'variables': variables
        }
        
    @staticmethod
    def __start(statement):
        """
        事务操作解析方法
        :param statement: 待解析语句
        :return:
        """
        statements = ' '.join(statement).split(';')

        return {
            'type': 'transaction',
            'statements': statements[1:-1]
        }