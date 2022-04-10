# -*- coding:utf-8 -*-
# @Time : 2022/4/10 8:15 下午
# @Author : huichuan LI
# @File : test1.py
# @Software: PyCharm
from huichuandb.engine import Engine
from huichuandb.core.field import Field, FieldType, FieldKey


e = Engine()                    # \u5b9e\u4f8b\u5316\u6570\u636e\u5e93\u5f15\u64ce\u5bf9\u8c61
e.create_database('test_db')    # \u521b\u5efa\u6570\u636e\u5e93 test_db
e.select_db('test_db')          # \u9009\u62e9\u6570\u636e\u5e93 test_db

e.create_table(
    name='t_test',
    f_id=Field(data_type=FieldType.INT, keys=[FieldKey.PRIMARY, FieldKey.INCREMENT]),
    f_name=Field(data_type=FieldType.VARCHAR, keys=FieldKey.NOT_NULL),
    f_age=Field(data_type=FieldType.INT, keys=FieldKey.NOT_NULL)
)

# \u5411\u6570\u636e\u8868 t_test \u4e2d\u63d2\u5165\u6570\u636e
e.insert(table_name='t_test', f_name='shiyanlou_001', f_age=20)
e.insert(table_name='t_test', f_name='shiyanlou_002', f_age=10)

ret = e.search('t_test')
for row in ret:
    print(row)

e.commit()