import re

from syldb.core import TYPE_MAP


def __is(data, condition):
    """等值判断"""
    # select * from t_test where f_id = 1;
    return data == condition


def __is_not(data, condition):
    """不等判断"""
    # select * from t_test where f_id != 1;
    return data != condition


def __in(data, condition):
    """包含判断"""
    # select * from t_test where f_id in 1,2;
    return data in condition


def __not_in(data, condition):
    """不包含判断"""
    # select * from t_test where f_id not in 1,2;
    return data not in condition


def __greater(data, condition):
    """大于判断"""
    # select * from t_test where f_id > 1;
    return data > condition


def __less(data, condition):
    """小于判断"""
    # select * from t_test where f_id < 1;
    return data < condition


def __greater_and_equal(data, condition):
    """大于或等于判断"""
    # select * from t_test where f_id >= 1;
    return data >= condition


def __less_and_equal(data, condition):
    """小于或等于判断"""
    # select * from t_test where f_id <= 1;
    return data <= condition


def __like(data, condition):
    """
    模糊匹配
    :param data: 待判断数据
    :param condition: 判断条件
    :return: 判断结果
    """
    # 将 '_' 标识符转为正则表达式 '.' 关键字
    condition = condition.strip("'").strip('"')  # 去除字符引号干扰
    condition = condition.replace('_', '.')
    tmp = condition.split('%')  # 依据通配符 '%' 切割匹配条件
    length = len(tmp)
    res = None
    if length == 3:
        # select * from t_test where f_name like '%shiyanlou%'
        res = re.search(tmp[1], data)

    elif length == 2:
        if ''.join(tmp) == '':
            # select * from t_table where t_name like '%';
            raise Exception('Matching condition error')

        elif tmp[0] == '':
            # select * from t_test where f_name like '%shiyanlou'
            res = re.search('^' + tmp[1], data)

        elif tmp[1] == '':
            # select * from t_test where f_name like 'shiyanlou%'
            res = re.search(tmp[0] + '$', data)

        else:
            raise Exception('Matching condition error')

    elif length == 1:
        # select * from t_table where t_name like 'shiyanlou';
        res = re.search(tmp[0], data)

    return res is not None


def __range(data, condition):
    """区间匹配"""
    # select * from t_test where f_id range (1,10);
    return condition[0] <= data <= condition[1]


SYMBOL_MAP = {
    'IN': __in,
    'NOT_IN': __not_in,
    '>': __greater,
    '<': __less,
    '=': __is,
    '!=': __is_not,
    '>=': __greater_and_equal,
    '<=': __less_and_equal,
    'LIKE': __like,
    'RANGE': __range,
}


class BaseCase:
    """条件判断基类"""

    def __init__(self, condition, symbol):
        """
        初始化条件基类
        :param condition: 判断条件
        :param symbol: 关键字
        """
        self.condition = condition
        self.symbol = symbol

    def __call__(self, data, data_type):
        """
        调用响应方法
        :param data: 待判断数据
        :param data_type: 数据类型
        :return:
        """
        self.condition = TYPE_MAP[data_type.value](self.condition)
        if isinstance(self.condition, str):
            # 如果为字符串格式，消去可能出现的引号
            self.condition = self.condition.replace("'", "").replace('"', '')

        return SYMBOL_MAP[self.symbol](data, self.condition)


class BaseListCase(BaseCase):
    """条件处理类，继承条件基类，将混合条件拆分为单个"""

    def __call__(self, data, data_type):
        """
        调用响应方法
        :param data: 待判断数据
        :param data_type: 数据类型
        :return:
        """
        if not isinstance(self.condition, list):
            raise TypeError(f'Condition type error.It must be {data_type}')

        conditions = []

        for value in self.condition:
            # 遍历所有条件
            value = TYPE_MAP[data_type.value](value)

            if isinstance(value, str):
                value = value.replace("'", "").replace('"', '')

            conditions.append(value)
        return SYMBOL_MAP[self.symbol](data, conditions)


class IsCase(BaseCase):
    """等值条件判断类"""

    def __init__(self, condition):
        super().__init__(condition, symbol='=')


class IsNotCase(BaseCase):
    """不等条件判断类"""

    def __init__(self, condition):
        super().__init__(condition, symbol='!=')


class InCase(BaseListCase):
    """包含条件判断类"""

    def __init__(self, condition):
        super().__init__(condition, symbol='IN')


class NotInCase(BaseListCase):
    """不包含条件判断类"""

    def __init__(self, condition):
        super().__init__(condition, symbol='NOT_IN')


class GreaterCase(BaseCase):
    """大于条件判断类"""

    def __init__(self, condition):
        super().__init__(condition, symbol='>')


class LessCase(BaseCase):
    """小于条件判断类"""

    def __init__(self, condition):
        super().__init__(condition, symbol='<')


class GAECase(BaseCase):
    """大于或等于条件判断类"""

    def __init__(self, condition):
        super().__init__(condition, symbol='>=')


class LAECase(BaseCase):
    """小于或等于条件判断类"""

    def __init__(self, condition):
        super().__init__(condition, symbol='<=')


class LikeCase(BaseCase):
    """模糊匹配条件判断类"""

    def __init__(self, condition):
        super().__init__(condition, symbol='LIKE')

    def __call__(self, data, data_type):
        self.condition = TYPE_MAP[data_type.value](self.condition)

        return SYMBOL_MAP[self.symbol](str(data), self.condition)


class RangeCase(BaseCase):
    """区间匹配条件判断类"""

    def __init__(self, start, end):
        super().__init__((float(start), float(end)), symbol='RANGE')

    def __call__(self, data, data_type):
        if not isinstance(self.condition, tuple):
            raise TypeError('not a tuple condition')

        return SYMBOL_MAP[self.symbol](data, self.condition)
