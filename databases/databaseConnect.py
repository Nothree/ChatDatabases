import mysql.connector
from py2neo import Graph

#连接mysql数据库的类
class MysqlConnect:
    def __init__(self, host, user, password, database, port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.conn = mysql.connector.connect(host=self.host, user=self.user, password=self.password, database=self.database, port=self.port)
        self.cursor = self.conn.cursor()

    def query(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    def close(self):
        self.cursor.close()
        self.conn.close()

#连接neo4j数据库的类
class Neo4jConnect:
    def __init__(self, profile, user, password):
        self.profile = profile
        self.user = user
        self.password = password
        self.graph = Graph(profile=self.profile, user=self.user, password=self.password)

    def query(self, sql):
        return self.graph.run(sql)

