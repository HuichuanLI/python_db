import re

from case import *

class SQLParser:
    def __init__(self):

        #
        self.__pattern_map = {
            'SELECT': r'(SELECT|select) (.*) (FROM|from) (.*)',
            'UPDATE': r'(UPDATE|update) (.*) (SET|set) (.*)',
            'INSERT': r'(INSERT|insert) (INTO|into) (.*)\((.*)\) (VALUES|values)\((.*)\)'
        }

        self.__action_map = {
            'SELECT': self.__select,
            'UPDATE': self.__update,
            'DELETE': self.__delete,
            'INSERT': self.__insert,
            'USE': self.__use,
            'EXIT': self.__exit,
            'QUIT': self.__exit,
            'SHOW': self.__show,
            'DROP': self.__drop
        }

        self.SYMBOL_MAP = {
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

    # 处理掉空格
    def __filter_space(self, obj):
        ret = []
        for x in obj:
            if x.strip() == '' or x.strip() == 'AND':
                continue
            ret.append(x)

        return ret

    # 解析语句
    def parse(self, statement):
        tmp_s = statement

        # 如果语句中有 where 操作符，
        if 'where' in statement:
            statement = statement.split("where")
        else:
            statement = statement.split("WHERE")

        # 基础的 SQL 语句都是空格隔开关键字，此处使用空格分隔 SQL 语句
        base_statement = self.__filter_space(statement[0].split(" "))

        # SQL 语句一般由最少三个关键字组成，这里设定长度小于 2 时，又非退出等命令，则为错误语法
        if len(base_statement) < 2 and base_statement[0] not in ['exit', 'quit']:
            raise Exception('Syntax Error for: %s' % tmp_s)

        # 在定义字典 __action_map 时，字典的键使用的是大写字符，此处转换为大写格式
        action_type = base_statement[0].upper()

        if action_type not in self.__action_map:
            raise Exception('Syntax Error for: %s' % tmp_s)

        # 根据字典得到对应的值
        action = self.__action_map[action_type](base_statement)

        if action is None or 'type' not in action:
            raise Exception('Syntax Error for: %s' % tmp_s)

        action['conditions'] = {}

        conditions = None

        if len(statement) == 2:
            conditions = self.__filter_space(statement[1].split(" "))

        if conditions:
            for index in range(0, len(conditions), 3):
                field = conditions[index]
                symbol = conditions[index + 1].upper()
                condition = conditions[index + 2]

                if symbol == 'RANGE':
                    condition_tmp = condition.replace("(", '').replace(")", '').split(",")
                    start = condition_tmp[0]
                    end = condition_tmp[1]
                    case = self.SYMBOL_MAP[symbol](start, end)
                elif symbol == 'IN' or symbol == 'NOT_IN':
                    condition_tmp = condition.replace("(", '').replace(")", '').replace(" ", '').split(",")
                    condition = condition_tmp
                    case = self.SYMBOL_MAP[symbol](condition)
                else:
                    case = self.SYMBOL_MAP[symbol](condition)

                action['conditions'][field] = case
        return action

    def __get_comp(self, action):
        return re.compile(self.__pattern_map[action])


    # 查询
    def __select(self, statement):
        comp = self.__get_comp('SELECT')
        ret = comp.findall(" ".join(statement))

        if ret and len(ret[0]) == 4:
            fields = ret[0][1]
            table = ret[0][3]

            if fields != '*':
                fields = [field.strip() for field in fields.split(",")]

            return {
                'type': 'search',
                'fields': fields,
                'table': table
            }

        return None

    # 更新
    def __update(self, statement):
        statement = ' '.join(statement)
        comp = self.__get_comp('UPDATE')
        ret = comp.findall(statement)
        if ret and len(ret[0]) == 4:
            data = {
                'type': 'update',
                'table': ret[0][1],
                'data': {}
            }
            set_statement = ret[0][3].split(",")
            for s in set_statement:
                s = s.split("=")
                field = s[0].strip()
                value = s[1].strip()
                if "'" in value or '"' in value:
                    value = value.replace('"', '').replace("'", '').strip()
                else:
                    try:
                        value = int(value.strip())
                    except:
                        return None
                data['data'][field] = value

            return data
        return None

    # 删除
    def __delete(self, statement):
        return {
            'type': 'delete',
            'table': statement[2]
        }

    # 插入
    def __insert(self, statement):
        comp = self.__get_comp('INSERT')
        ret = comp.findall(" ".join(statement))

        if ret and len(ret[0]) == 6:
            ret_tmp = ret[0]
            data = {
                'type': 'insert',
                'table': ret_tmp[2],
                'data': {}
            }
            fields = ret_tmp[3].split(",")
            values = ret_tmp[5].split(",")

            for i in range(0, len(fields)):
                field = fields[i]
                value = values[i]
                if "'" in value or '"' in value:
                    value = value.replace('"', '').replace("'", '').strip()
                else:
                    try:
                        value = int(value.strip())
                    except:
                        return None
                data['data'][field] = value
            return data
        return None

    # 选择使用的数据库
    def __use(self, statement):
        return {
            'type': 'use',
            'database': statement[1]
        }

    # 退出
    def __exit(self, _):
        return {
            'type': 'exit'
        }

    # 查看数据库列表或数据表 列表
    def __show(self, statement):
        kind = statement[1]

        if kind.upper() == 'DATABASES':
            return {
                'type': 'show',
                'kind': 'databases'
            }
        if kind.upper() == 'TABLES':
            return {
                'type': 'show',
                'kind': 'tables'
            }

    # 删除数据库或数据表
    def __drop(self, statement):
        kind = statement[1]

        if kind.upper() == 'DATABASE':
            return {
                'type': 'drop',
                'kind': 'database',
                'name': statement[2]
            }
        if kind.upper() == 'TABLE':
            return {
                'type': 'drop',
                'kind': 'table',
                'name': statement[2]
            }