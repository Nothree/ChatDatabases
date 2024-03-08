import mysql.connector
from py2neo import Graph

# 连接到Neo4j数据库
graph = Graph("bolt://localhost:7687", user="neo4j", password="jx880918")
#清空neo4j数据库
query = "MATCH (n) DETACH DELETE n"
graph.run(query)

# port = 33062
# host = "113.66.113.0"
port = 3306
host = "192.168.0.118"
# 建立数据库连接
conn = mysql.connector.connect(
    host=host,  # 数据库主机地址
    user="root",  # 数据库用户名
    port=port,
    password="broadtech",  # 数据库密码
    database="chatiot"  # 数据库名称
)
# 创建游标对象
cursor = conn.cursor()

# 执行查询语句获取所有表格信息
cursor.execute("SHOW TABLES")

# 获取查询结果
tables = cursor.fetchall()

# 遍历tables列表，创建节点
for table in set(tables):
    # 构建Cypher查询
    query = f"CREATE (t:Table {{name: '{str(table[0])}'}})"
    # 执行查询
    graph.run(query)

fieldsBuffer = []
# 遍历每个表格
for table in tables:
    table_name = table[0]
    # 执行查询语句获取每个表的字段信息
    cursor.execute(f"SHOW FULL COLUMNS FROM {table_name}")
    # 获取字段信息
    fields = cursor.fetchall()
    fieldsBuffer += fields

# 遍历打印每个字段的名称、描述
for field in set(fieldsBuffer):
    field_name = field[0]
    field_comment = field[8]
    query = f"CREATE (t:Field {{name: '{str(field_name)}', comment: '{str(field_comment)}'}})"
    graph.run(query)

# 遍历每个表格
for table in tables:
    table_name = table[0]
    # 执行查询语句获取每个表的字段信息
    cursor.execute(f"SHOW FULL COLUMNS FROM {table_name}")
    # 获取字段信息
    fields = cursor.fetchall()
    # 遍历每个字段,创建表和字段的关系
    for field in fields:
        # 表和字段的属性值
        field_name = field[0]
        field_comment = field[8]
        # 创建关系
        query = f"MATCH (t:Table {{name: '{table_name}'}}), (f:Field {{name: '{field_name}', comment: '{field_comment}'}}) CREATE (t)-[:contain]->(f)"
        graph.run(query)

# 执行Cypher查询
query = "MATCH (n:Table) RETURN n LIMIT 25"
result = graph.run(query)

# 处理查询结果
for record in result:
    print(record)

# 关闭游标和数据库连接
cursor.close()
conn.close()

#构建表的血缘关系知识图谱
# 建立数据库连接
conn = mysql.connector.connect(
    host=host,  # 数据库主机地址
    user="root",  # 数据库用户名
    port=port,
    password="broadtech",  # 数据库密码
    database="chatiot_conf"  # 数据库名称
)
# 创建游标对象
cursor = conn.cursor()

# 执行查询语句获取所有表格信息
cursor.execute("select table_relation from table_relation")

# 获取查询结果
tableRelations = cursor.fetchall()

for tableRelation in set(tableRelations):
    # 构建Cypher查询
    tableRelationStr = str(tableRelation[0])
    # tableRelationStr字符串用"->"分隔，生成新的列表
    tableRelationList = tableRelationStr.split("->")
    # 遍历tableRelationList，将当前的元素与下一个元素连接，生成neo4j的图关系，关系名称为"father_of"
    for i in range(len(tableRelationList) - 1):
        # 获取当前元素和下一个元素
        currentElement = tableRelationList[i]
        nextElement = tableRelationList[i + 1]
        # 创建关系
        query = f"MATCH (t:Table {{name: '{currentElement}'}}),(f:Table {{name: '{nextElement}'}}) CREATE (t)-[:father_of]->(f)"
        graph.run(query)
    # query = f"CREATE (t:Table {{name: '{str(tableRelation[0])}'}})"
    # # 执行查询
    # graph.run(query)

