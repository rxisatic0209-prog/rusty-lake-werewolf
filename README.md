# 锈湖狼人杀

一个基于 AutoGen 的 6 人局狼人杀实验项目。

项目把锈湖风格的叙事提示词、身份人设、狼人杀规则和工具调用拆开组织，让 5 个 AI 玩家加 1 个真人席位在同一局中进行夜晚行动、白天发言和投票。

## 当前设定

- 固定 6 人局：2 狼 + 4 好人
- `P1` 固定为真人席位，使用 `UserProxyAgent`
- `P2-P6` 为 AI 玩家
- `Mr_Owl` 为固定上帝
- 身份卡和身份人设已拆分，分别由 `roles.py` 和 `personas.py` 管理

## 目录结构

- `main.py`：游戏主流程，负责发身份、实例化 Agent、推进夜晚和白天回合
- `config.py`：模型客户端配置和全局锈湖风格提示词
- `roles.py`：身份卡定义，例如狼人、女巫、预言家、乌鸦、猎人、平民
- `personas.py`：身份对应的人设、说话风格和行为原则
- `rules.py`：整局状态、夜晚/白天结算、投票和胜负判断
- `regis.py`：给 Agent 调用的工具箱，例如杀人、查验、诅咒、投票

## 环境变量

项目通过 `.env` 读取模型配置：

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=your_base_url
LLM_MODEL_ID=your_model_id
```

## 安装依赖

如果你不用仓库里现成的 `venv`，至少需要这些依赖：

```bash
pip install openai python-dotenv autogen-agentchat autogen-ext[openai]
```

推荐使用 Python 3.11。

## 运行方式

如果已经有本地虚拟环境：

```bash
./venv/bin/python main.py
```

或者使用你自己的 Python 环境：

```bash
python main.py
```

## 运行流程

1. 系统随机发放 6 张身份卡
2. `P1` 抽到其中一张，作为真人玩家参与
3. 夜晚阶段依次处理狼人、预言家、女巫、乌鸦
4. 天亮后结算死亡
5. 白天阶段进行发言和投票
6. 直到某一阵营满足胜利条件

## 已知限制

- 当前运行依赖外部模型接口，若供应商限流，整局可能中断
- `P1` 是真人席位，因此运行过程中会需要本地输入
- 项目目前没有 `requirements.txt`，依赖版本以你本地环境为准

## 适合继续扩展的方向

- 为座位再增加一层独立人格，而不仅是身份人格
- 增加 `README` 之外的 `requirements.txt` 或 `pyproject.toml`
- 给限流和模型故障加自动重试
- 增加更多角色和规则变体
