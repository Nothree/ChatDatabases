# askToPrompt.py
# Created by Nothree on 2024/3/6.
# 功能：
# 从用户提问转为LLM的prompt
from databases.databaseConnect import MysqlConnect
import re
from py2neo import Graph
import json
import logging_config
from dotenv import load_dotenv, find_dotenv
import os

_ = load_dotenv(find_dotenv())

class AskToPrompt:
    def __init__(self):
        self.mysql_host = os.getenv("mysql_host")
        self.mysql_database_conf = os.getenv("mysql_database_conf")
        self.mysql_user = os.getenv("mysql_user")
        self.mysql_password = os.getenv("mysql_password")
        self.neo4j_password = os.getenv("neo4j_password")
        self.neo4j_user = os.getenv("neo4j_user")
        self.graph = Graph("bolt://localhost:7687", user=self.neo4j_user, password=self.neo4j_password)
        self.mysqlConn = MysqlConnect(host=self.mysql_host, user=self.mysql_user, password=self.mysql_password, database=self.mysql_database_conf)

    def close_mysql(self):
        self.mysqlConn.close()

    # 判断是否祖父关系
    def __is_father(self, table_name, father_table_name):
        query = """
        MATCH (table_name:Table {name: '%s'})-[:father_of*]->(father_table_name:Table {name: '%s'})
        RETURN father_table_name.name
        """ % (table_name, father_table_name)
        result = self.graph.run(query)
        for record in result:
            return True
        return False

    # 生成sql建表语句
    def __create_table(self, table_name, table_fields):
        result = f"CREATE TABLE {table_name} (\n"
        for field in table_fields:
            field_name = field
            field_comment = table_fields[field]
            result += f"    {field_name} COMMENT {field_comment},\n"
        result = result.rstrip(",\n") + "\n)"
        return result

    # 将user question匹配到的表的字段，通过知识图谱关联出字段对应的表
    def __get_table_contain_field(self, results, user_question):
        # 将结果赋值给Python变量
        fields = [row[0] for row in results]
        comments = [row[1] for row in results]

        # 遍历fields和comments列表进行匹配
        table_contain_field = []
        for i in range(len(fields)):
            field = fields[i]
            comment = comments[i]

            # 使用正则表达式匹配用户提问
            if re.search(field, user_question.lower()):
                comment_json = json.loads(comment)

                if 'field' in comment_json:
                    comment_field = comment_json['field']
                    # 执行Cypher查询
                    query = f"""
                    MATCH (table:Table)-[connect:contain]->(field:Field)
                    WHERE field.name IN ["{comment_field}"]
                    RETURN connect
                    """
                    result = self.graph.run(query)

                    # 处理查询结果
                    for record in result:
                        table_contain_field.append(str(record))
        return table_contain_field

    # 将user question匹配到的表的字段，通过知识图谱关联出字段对应的表
    def __get_table_name(self, results, user_question):
        # 将结果赋值给Python变量
        tables = [row[0] for row in results]
        comments = [row[1] for row in results]

        # 遍历fields和comments列表进行匹配
        table_names = []
        for i in range(len(tables)):
            table = tables[i]
            comment = comments[i]

            # 使用正则表达式匹配用户提问
            if re.search(table, user_question.lower()):
                comment_json = json.loads(comment)

                if 'table' in comment_json:
                    comment_table = comment_json['table']
                    table_names.append(str(comment_table))
        return table_names

    def get_prompt(self, user_question):
        # 提取表字段
        query = "SELECT DISTINCT field, comment FROM field_regular"
        results = self.mysqlConn.query(query)
        # 将user question匹配到的表的字段，通过知识图谱关联出字段对应的表
        table_contain_field = self.__get_table_contain_field(results, user_question)

        # 提取表名称
        query = "SELECT DISTINCT table_name, comment FROM table_regular"
        results = self.mysqlConn.query(query)
        # 将user question与表列表进行正则表达式匹配
        question_table_names = self.__get_table_name(results, user_question)

        # 将知识图谱的关系转为table_field字典
        table_field = {}

        logging_config.logging.info(table_contain_field)

        for item in table_contain_field:
            table_name = item.split("'Table', name='")[1].split("'")[0]
            field_name = item.split("'Field',")[1].split("name='")[1].split("'")[0]
            field_comment = item.split("'Field',")[1].split("comment='")[1].split("'")[0]

            if table_name not in table_field:
                table_field[table_name] = {}

            table_field[table_name][field_name] = field_comment
        logging_config.logging.info(table_field)
        # 取table_field[table_name]字典的个数最多的table_name字典，用for循环实现
        table_list = list(set(table_field.keys()))
        table_disabled = []
        for i in range(len(table_list)):
            if i in table_disabled:
                continue
            for j in range(i + 1, len(table_list)):
                if self.__is_father(table_list[i], table_list[j]):
                    if len(table_field[table_list[i]]) >= len(table_field[table_list[j]]):
                        table_disabled.append(j)
                    else:
                        table_disabled.append(i)
                        break
                elif self.__is_father(table_list[j], table_list[i]):
                    if len(table_field[table_list[j]]) >= len(table_field[table_list[i]]):
                        table_disabled.append(i)
                        break
                    else:
                        table_disabled.append(j)

        logging_config.logger.info('table_disabled:'+str(table_disabled))

        create_table = ""
        for i in range(len(table_list)):
            if i in table_disabled:
                continue
            table_name = table_list[i]
            table_fields = table_field[table_name]
            create_table += self.__create_table(table_name, table_fields) + "\n"
        return create_table
