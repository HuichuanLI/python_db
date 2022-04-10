# -*- coding:utf-8 -*-
# @Time : 2022/4/10 8:39 下午
# @Author : huichuan LI
# @File : test2.py
# @Software: PyCharm
from huichuandb.engine import Engine
from huichuandb.case import *

e = Engine()                    # 实例化数据库引擎对象
e.select_db('test_db')          # 选择数据库 test_db

# 向表 `t_test` 中添加一些数据
e.insert(table_name='t_test', f_name='shiyanlou_003', f_age=30)
e.insert(table_name='t_test', f_name='shiyanlou_004', f_age=40)
e.insert(table_name='t_test', f_name='xiaoming', f_age=50)
e.insert(table_name='t_test', f_name='echo', f_age=50)


print("-"*5, "这里是表 t_test 的全部数据", "-"*5)
all_data = e.search("t_test")
for i in all_data:
    print(i)
print("-" * 30)


print("-"*5, "查询年龄在三十岁以上的用户", "-"*5)
test1_data = e.search(table_name="t_test", f_age=GreaterCase(30))
for i in test1_data:
    print(i)
print("-" * 30)

# 保存更改到数据库中
e.commit()