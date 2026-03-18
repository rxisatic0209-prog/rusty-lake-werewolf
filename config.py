import os
from dotenv import load_dotenv
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo

load_dotenv()

RUSTY_STYLE = """
[环境：锈湖往生室] 
你的语气：阴冷、碎片化、充满隐喻。严禁使用现代社交辞令。
核心逻辑：生命只是方块的载体，死亡是提取的开始。
常用意象：钟表、蝉、黑色方块、倒影、湖水、记忆提取。
"""

# 从 .env 读取配置
api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")
model_id = os.getenv("LLM_MODEL_ID")

# 实例化模型客户端
model_client = OpenAIChatCompletionClient(
    model=model_id, 
    api_key=api_key,
    base_url=base_url,
    model_info=ModelInfo(
        vision=True, 
        function_calling=True, 
        json_output=True, 
        family="gpt-4o",
        structured_output=True # 解决新版 AutoGen 警告
    )
)