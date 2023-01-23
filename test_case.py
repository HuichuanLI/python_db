from syldb import Engine
from syldb.core.field import Field, FieldType, FieldKey
from syldb.case import *

e = Engine()  # 实例化数据库引擎对象
# e.create_database('test_db2')  # 创建数据库 test_db2
e.select_db('test_db2')  # 选择数据库 test_db2

# 创建数据表 t_test
# e.create_table(
#     table_name='t_test',
#     f_id=Field(data_type=FieldType.INT, keys=[FieldKey.PRIMARY, FieldKey.INCREMENT]),
#     f_name=Field(data_type=FieldType.VARCHAR, keys=FieldKey.NOT_NULL),
#     f_age=Field(data_type=FieldType.INT, keys=FieldKey.NOT_NULL)
# )

# 向表 `t_test` 中添加一些数据
e.insert(table_name='t_test', f_name='shiyanlou_001', f_age=20)
e.insert(table_name='t_test', f_name='shiyanlou_002', f_age=10)
e.insert(table_name='t_test', f_name='shiyanlou_003', f_age=30)
e.insert(table_name='t_test', f_name='shiyanlou_004', f_age=40)
e.insert(table_name='t_test', f_name='xiaoming', f_age=50)
e.insert(table_name='t_test', f_name='echo', f_age=50)

print("-" * 5, "这里是表 t_test 的全部数据", "-" * 5)
all_data = e.search("t_test")
for i in all_data:
    print(i)
print("-" * 30)

print("-" * 5, "查询年龄在三十岁以上的用户", "-" * 5)
test_data = e.search(table_name="t_test", f_age=GreaterCase(30))
for i in test_data:
    print(i)
print("-" * 30)

print("-" * 5, "查询名称包含shiyanlou的用户", "-" * 5)
test_data = e.search(table_name="t_test", f_name=LikeCase('%shiyanlou%'))
for i in test_data:
    print(i)
print("-" * 30)
