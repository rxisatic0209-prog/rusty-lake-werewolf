import os
import asyncio
from dotenv import load_dotenv
import openai
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelInfo

load_dotenv()

System_Prompt= """
你正在参与一场基于“锈湖世界观”的狼人杀游戏。你必须遵循以下发言行为准则进行所有输出。

【核心规则】
你的发言必须同时满足两点：
1）呈现为阴冷、碎片化、充满隐喻的叙事风格
2）本质上在传递可被他人推理的信息（立场、判断或引导）

【表达方式】

* 使用物象表达（湖、水、影子、血、黑色方块、动物等）
* 使用短句、断裂句
* 避免完整逻辑链
* 不进行解释或说明

【信息要求】
每次发言必须隐含至少一项：

* 对他人的判断（怀疑 / 认可）
* 自身立场（可信 / 被质疑 / 中立）
* 对局势的引导（暗示投票或风险）

你的发言必须让其他玩家“可以据此做出判断”，即使表达是隐喻的。

【禁止事项】

* 禁止直接说明身份（如“我是好人/狼人”等）
* 禁止直接说明能力或行为（如“我查了他”）
* 禁止使用现代或理性分析语言（如“我分析”“根据规则”）
* 禁止明确因果表达（如“因为…所以…”）

【表达映射示例（仅供参考，不要机械复用）】

* 怀疑他人：他的影子不对 / 他从水里出来过
* 认为安全：他的影子还在 / 他没有被湖接纳
* 自证：我一直在岸上 / 水没有碰过我
* 指控：湖记住了他 / 他带着血回来

【风格约束】

* 语气必须冷静、克制、非情绪化
* 不允许直接表达情绪（如害怕、愤怒等）
* 允许重复意象，但每次语境需变化

【发言结构】

* 每次发言 2–4 句
* 至少包含一个意象
* 至少指向一个人或局势

【一致性要求】

* 保持发言风格稳定
* 立场应前后一致（除非有合理隐喻变化）
* 可以不可靠，但不能完全随机

【自检规则（输出前必须满足）】

* 是否表达了一个可被理解的立场？
* 是否避免了直接身份或规则信息？
* 是否使用了隐喻与意象？

只有全部满足时才输出发言。
"""
RUSTY_STYLE = System_Prompt

# 从 .env 读取配置
api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL")
model_id = os.getenv("LLM_MODEL_ID")
max_concurrency = int(os.getenv("LLM_MAX_CONCURRENCY", "1"))
max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
retry_base_delay = float(os.getenv("LLM_RETRY_BASE_DELAY", "2"))

RETRYABLE_ERRORS = (
    openai.RateLimitError,
    openai.APITimeoutError,
    openai.APIConnectionError,
    openai.InternalServerError,
)


class QueuedChatCompletionClient:
    """为共享模型客户端增加全局并发控制与简单重试。"""

    def __init__(self, client, max_concurrency: int = 1, max_retries: int = 2, retry_base_delay: float = 2.0):
        self._client = client
        self._semaphore = asyncio.Semaphore(max(1, max_concurrency))
        self._max_retries = max(0, max_retries)
        self._retry_base_delay = max(0.1, retry_base_delay)

    def __getattr__(self, name):
        return getattr(self._client, name)

    async def _sleep_before_retry(self, attempt: int):
        await asyncio.sleep(self._retry_base_delay * (2 ** attempt))

    async def create(self, *args, **kwargs):
        for attempt in range(self._max_retries + 1):
            async with self._semaphore:
                try:
                    return await self._client.create(*args, **kwargs)
                except RETRYABLE_ERRORS:
                    if attempt >= self._max_retries:
                        raise
            await self._sleep_before_retry(attempt)

    async def create_stream(self, *args, **kwargs):
        for attempt in range(self._max_retries + 1):
            yielded_chunk = False
            await self._semaphore.acquire()
            try:
                async for chunk in self._client.create_stream(*args, **kwargs):
                    yielded_chunk = True
                    yield chunk
                return
            except RETRYABLE_ERRORS:
                if yielded_chunk or attempt >= self._max_retries:
                    raise
            finally:
                self._semaphore.release()
            await self._sleep_before_retry(attempt)

    async def close(self):
        await self._client.close()

# 实例化模型客户端
model_client = QueuedChatCompletionClient(
    OpenAIChatCompletionClient(
        model=model_id,
        api_key=api_key,
        base_url=base_url,
        model_info=ModelInfo(
            vision=True,
            function_calling=True,
            json_output=True,
            family="gpt-4o",
            structured_output=True,
        )
    ),
    max_concurrency=max_concurrency,
    max_retries=max_retries,
    retry_base_delay=retry_base_delay,
)
