from askToPrompt import AskToPrompt
from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv, find_dotenv
import logging_config

_ = load_dotenv(find_dotenv())

ask_to_prompt = AskToPrompt()

while True:
    #获取用户从命令行输入
    user_question = input("请输入您的问题：")
    # user_question = "统计apn、iotsubcode维度的TCP连接成功率""统计iotsubcode、域名维度的HTTP请求成功率"
    create_table = ask_to_prompt.get_prompt(user_question)

    llm = ChatOpenAI(model="gpt-3.5-turbo")  # 默认是gpt-3.5-turbo
    systemTemplate = f"""
    请根据用户选择的mysql数据库和该库的部分可用表结构定义来回答用户问题.
    数据库名:
        chatiot
    表结构定义:
    {create_table}
    当需要统计时，使用group by语句进行统计
    
    约束:
        1. 请根据用户问题理解用户意图，使用给出表结构定义创建一个语法正确的 mysql sql，如果不需要sql，则直接回答用户问题。
        2. 除非用户在问题中指定了他希望获得的具体数据行数，否则始终将查询限制为最多 50 个结果。
        3. 只能使用表结构信息中提供的表来生成 sql，如果无法根据提供的表结构中生成 sql ，请说：“提供的表结构信息不足以生成 sql 查询。” 禁止随意捏造信息。
        4. 请注意生成SQL时不要弄错表和列的关系
        5. 请检查SQL的正确性，并保证正确的情况下优化查询性能
    """
    logging_config.logger.info(systemTemplate)
    template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(systemTemplate),
            HumanMessagePromptTemplate.from_template("用户问题:\n{query}"),
        ]
    )

    prompt = template.format_messages(
            query=user_question
        )

    print(llm.invoke(prompt))

