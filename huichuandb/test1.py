# -*- coding:utf-8 -*-
# @Time : 2022/4/10 8:15 下午
# @Author : huichuan LI
# @File : test1.py
# @Software: PyCharm
from huichuandb import Engine
from huichuandb.core.field import Field, FieldType, FieldKey


e = Engine()
e.create_database('test_db')
e.select_db('test_db')

e.create_table(
    name='t_test',
    f_id=Field(data_type=FieldType.INT, keys=[FieldKey.PRIMARY, FieldKey.INCREMENT]),
    f_name=Field(data_type=FieldType.VARCHAR, keys=FieldKey.NOT_NULL)
)

e.insert(table_name='t_test', f_name='shiyanlou_001')
e.insert(table_name='t_test', f_name='shiyanlou_002')

ret = e.search('t_test')
for row in ret:
    print(row)