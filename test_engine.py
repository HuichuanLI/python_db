from syldb import Engine
from syldb.core.field import Field, FieldType, FieldKey

e = Engine()  # 实例化数据库引擎对象

e.create_database('test_db')  # 创建数据库 test_db
e.select_db('test_db')  # 选择数据库 test_db

# 创建一张名为 t_test 的数据表，它有两个字段，一个是 f_id 和 f_name
e.create_table(
    table_name='t_test',
    f_id=Field(data_type=FieldType.INT, keys=[FieldKey.PRIMARY, FieldKey.INCREMENT]),
    f_name=Field(data_type=FieldType.VARCHAR, keys=FieldKey.NOT_NULL)
)

# 向数据表 t_test 中插入数据
e.insert(table_name='t_test', f_name='shiyanlou_001')
e.insert(table_name='t_test', f_name='shiyanlou_002')

# 查询 t_test 表中的数据，并打印出来
ret = e.search('t_test')
for row in ret:
    print(row)
