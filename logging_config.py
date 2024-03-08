import logging

# 配置日志输出的格式和级别
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# 创建全局日志对象
logger = logging.getLogger(__name__)
