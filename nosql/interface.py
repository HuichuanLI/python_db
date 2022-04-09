# -*- coding:utf-8 -*-
# @Time : 2022/4/7 12:26 上午
# @Author : huichuan LI
# @File : interface.py
# @Software: PyCharm
from binary_tree import BinaryTree
from physical import Storage


class DBDB(object):

    def __init__(self, f):
        self._storage = Storage(f)
        self._tree = BinaryTree(self._storage)

    def _assert_not_closed(self):
        if self._storage.closed:
            raise ValueError('Database closed.')

    def close(self):
        self._storage.close()

    def commit(self):
        self._assert_not_closed()
        self._tree.commit()

    def __getitem__(self, key):
        # 通过 db[key] 获取键值
        self._assert_not_closed()
        return self._tree.get(key)

    def __setitem__(self, key, value)
        # 通过 db[key] = value 设置键值
        self._assert_not_closed()
        return self._tree.set(key, value)

    def __delitem__(self, key):
        # 通过 del db[key] 删除键值
        self._assert_not_closed()
        return self._tree.pop(key)

    def __contains__(self, key):
        #通过 key in db 来判断键在不在数据库中
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def __len__(self):
        return len(self._tree)
