# ClothWorkFlow 技术原理与实操指南

## 目录

1. [项目总览](#1-项目总览)
2. [系统架构](#2-系统架构)
3. [环境准备与配置](#3-环境准备与配置)
4. [Step 1：网页爬取（browser-use + Claude）](#4-step-1网页爬取)
5. [Step 2：AI 服装分析（Gemini 多模态）](#5-step-2ai-服装分析)
6. [Step 3：索引构建（BGE-M3 + BM25）](#6-step-3索引构建)
7. [Step 4：混合检索推荐（4 阶段 Pipeline）](#7-step-4混合检索推荐)
8. [Web 界面与 API](#8-web-界面与-api)
9. [常见问题与排障](#9-常见问题与排障)

---

## 1. 项目总览

ClothWorkFlow 是一个端到端的 **服装图片智能推荐系统**，覆盖从数据采集到用户交互的完整链路：

```
1688 店铺图片爬取 → Gemini AI 50+ 维度特征分析 → 向量 + 关键词混合索引 → 自然语言智能推荐
```

### 1.1 核心能力

| 能力 | 说明 |
|------|------|
| **智能爬取** | AI Agent 驱动浏览器，自动处理弹窗、懒加载、反爬 |
| **多模态分析** | Gemini 2.5 Flash 对服装图片做 50+ 维度结构化特征提取 |
| **混合检索** | BM25 关键词 + BGE-M3 语义向量 + RRF 融合 + Reranker 精排 |
| **可视化界面** | React + Ant Design 前端 + FastAPI 后端 |

### 1.2 技术栈一览

| 层级 | 技术 | 作用 |
|------|------|------|
| 爬取 | browser-use + Playwright + AWS Bedrock Claude | AI 驱动浏览器自动化 |
| 分析 | Gemini 2.5 Flash (OpenRouter) | 多模态图片理解 |
| 分词 | jieba + 服装领域自定义词典 | 中文关键词分词 |
| 向量 | BGE-M3 (1024 维) | 语义 Embedding |
| 关键词 | BM25Okapi | 传统关键词检索 |
| 精排 | BGE-Reranker-v2-M3 | 交叉编码器重排序 |
| 后端 | FastAPI (端口 8000) | REST API |
| 前端 | React 19 + TypeScript + Vite + Ant Design 6 | 交互界面 |
| 运行时 | Python >= 3.13, uv 包管理 | 项目环境 |

### 1.3 数据规模

项目包含预置的完整数据集：
- **4 个** 1688 服装店铺
- **433 张** 商品主图
- **432 条** AI 分析结果（JSON 格式）
- 预构建的向量索引 + BM25 语料库

---

## 2. 系统架构

### 2.1 整体数据流

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ClothWorkFlow 数据流                            │
│                                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │  Step 1   │    │   Step 2      │    │   Step 3      │    │  Step 4   │  │
│  │  网页爬取  │ ──→│  AI 特征分析  │ ──→│  索引构建     │ ──→│  混合检索  │  │
│  │           │    │              │    │              │    │           │  │
│  │ browser-  │    │ Gemini 2.5   │    │ BGE-M3 向量   │    │ BM25      │  │
│  │ use Agent │    │ Flash 多模态  │    │ + BM25 语料   │    │ + 向量    │  │
│  │ + Claude  │    │ 50+ 维度提取  │    │ 增量构建      │    │ + RRF     │  │
│  │ + Playw.  │    │ via OpenRouter│    │              │    │ + Reranker│  │
│  └──────────┘    └──────────────┘    └──────────────┘    └───────────┘  │
│       │                │                    │                   │        │
│       ▼                ▼                    ▼                   ▼        │
│  downloaded_      analysis/            _vector_index.npz     搜索结果    │
│  images/          *.json               _bm25_corpus.json     Top N 推荐  │
│  product_001.jpg  (结构化特征)          _vector_meta.json                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 文件结构与职责

```
ClothWorkFlow/
├── clothworkflow/                     # 主包
│   ├── core/                          # 核心逻辑层
│   │   ├── config.py                  #   统一配置（环境变量 > YAML > 默认值）
│   │   ├── llm_bedrock.py             #   AWS Bedrock LLM 适配器（Bearer Token 认证）
│   │   ├── analyzer.py                #   Gemini 多模态分析（50+ 维度 Prompt）
│   │   ├── text_builder.py            #   语义文本生成 + jieba 中文分词
│   │   ├── indexer.py                 #   向量索引 + BM25 语料构建（增量检测）
│   │   ├── retriever.py               #   4 阶段混合检索 Pipeline
│   │   └── model_manager.py           #   BGE 模型自动下载 / 路径管理
│   │
│   ├── cli/                           # CLI 入口层
│   │   ├── scrape.py                  #   爬取命令
│   │   ├── analyze.py                 #   分析命令
│   │   ├── recommend.py               #   推荐命令（支持交互模式）
│   │   └── pipeline.py                #   一键全流程
│   │
│   ├── api.py                         # FastAPI 后端（REST API）
│   ├── data/taget_url.txt             # 目标店铺 URL 列表
│   ├── analysis/                      # 全量分析结果（432 条）
│   └── web/                           # React 前端
│
├── downloaded_images/                 # 爬取的图片（按店铺子目录）
├── config.yaml                        # 项目配置文件
├── .env                               # 环境变量（API 密钥）
└── pyproject.toml                     # 依赖定义
```

### 2.3 配置优先级机制

项目采用三层配置覆盖体系，由 `core/config.py` 统一管理：

```
环境变量（最高优先级）
    ↓ 未设置则回退
config.yaml（中间优先级）
    ↓ 未设置则回退
代码默认值（兜底）
```

实现原理：

```python
def _get(section, key, env_var=None, default=None):
    # 1. 优先读环境变量
    if env_var:
        env_val = os.getenv(env_var)
        if env_val: return env_val
    # 2. 其次读 YAML
    yaml_val = _CFG.get(section, {}).get(key)
    if yaml_val is not None and yaml_val != "":
        return yaml_val
    # 3. 兜底默认值
    return default
```

这意味着你可以：
- **开发环境**：直接编辑 `.env` 或 `config.yaml`
- **CI/Docker**：通过环境变量注入，无需改文件
- **快速测试**：什么都不配，用代码默认值

---

## 3. 环境准备与配置

### 3.1 安装依赖

```bash
# 核心依赖（分析 + 推荐 + Web 界面）
uv sync

# 爬取功能的额外依赖（browser-use + playwright）
uv sync --extra scrape
uv run playwright install chromium
```

依赖分组说明（见 `pyproject.toml`）：

| 分组 | 包 | 用途 |
|------|-----|------|
| 核心 | httpx, jieba, numpy, rank-bm25, sentence-transformers, huggingface-hub | 分析/检索/模型 |
| scrape (可选) | browser-use[aws], playwright | 爬取功能 |

> **为什么爬取依赖是可选的？** browser-use 和 playwright 体积较大（~200MB），且需要下载 Chromium 浏览器。如果你只想使用推荐功能（项目已包含预置数据），可以跳过安装。

### 3.2 环境变量配置

```bash
cp .env.example .env
```

| 变量 | 用途 | 必需场景 |
|------|------|---------|
| `AWS_BEARER_TOKEN_BEDROCK` | AWS Bedrock 认证令牌 | 爬取（Step 1） |
| `AWS_REGION` | AWS 区域（默认 us-east-1） | 爬取（Step 1） |
| `OPENROUTER_API_KEY` | OpenRouter API 密钥 | AI 分析（Step 2） |
| `BGE_M3_PATH` | BGE-M3 模型本地路径（可选） | 自定义模型路径 |
| `BGE_RERANKER_PATH` | BGE-Reranker 本地路径（可选） | 自定义模型路径 |

### 3.3 config.yaml 完整配置项

```yaml
# API 密钥
api:
  openrouter_api_key: ""              # 或环境变量 OPENROUTER_API_KEY
  aws_bearer_token: ""                # 或环境变量 AWS_BEARER_TOKEN_BEDROCK
  aws_region: "us-east-1"             # 或环境变量 AWS_REGION

# 模型配置
models:
  analysis_model: "google/gemini-2.5-flash"                             # 分析模型
  bedrock_model: "bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0" # 爬取模型
  bge_m3_path: "BAAI/bge-m3"                                           # Embedding 模型
  bge_reranker_path: "BAAI/bge-reranker-v2-m3"                         # Reranker 模型

# 路径
paths:
  url_file: "clothworkflow/data/taget_url.txt"    # 目标 URL 文件
  download_dir: "downloaded_images"                # 图片保存目录
  analysis_dir: "clothworkflow/analysis"           # 分析结果目录

# 爬取参数
scrape:
  max_steps: 50            # Agent 最大操作步数（复杂页面可调大）
  min_image_size: 10240    # 图片过滤阈值（字节），低于此值丢弃
  headless: false          # false = 弹出浏览器窗口，可视化 Agent 操作

# 分析参数
analyze:
  timeout: 120             # API 请求超时（秒）
  delay: 1.0               # 批量请求间隔（秒），避免 API 限流
  max_tokens: 4096         # LLM 最大输出 token
  temperature: 0.1         # 温度越低，输出越稳定

# 推荐参数
recommend:
  top_n: 5                 # 默认推荐数量
  bm25_k: 15               # BM25 召回候选数
  vector_k: 15             # 向量召回候选数
  rerank_k: 20             # 送入 Reranker 的候选数
  rrf_k: 60                # RRF 融合常数（越大排名越均匀）
```

### 3.4 本地模型（首次自动下载）

| 模型 | HuggingFace ID | 大小 | 用途 |
|------|---------------|------|------|
| BGE-M3 | `BAAI/bge-m3` | ~2.2 GB | 语义 Embedding（1024 维向量） |
| BGE-Reranker-v2-M3 | `BAAI/bge-reranker-v2-m3` | ~1.1 GB | 交叉编码器精排 |

下载逻辑（`core/model_manager.py`）：

```
1. 检查 config 中配置的路径是否存在 config.json → 存在则直接使用
2. 检查项目 models/ 目录下是否已下载 → 存在则使用
3. 以上都没有 → 调用 huggingface_hub.snapshot_download() 自动下载到 models/
```

如果网络访问 HuggingFace 困难，可以手动下载后设置环境变量：

```bash
export BGE_M3_PATH="/your/local/path/bge-m3"
export BGE_RERANKER_PATH="/your/local/path/bge-reranker-v2-m3"
```

---

## 4. Step 1：网页爬取

### 4.1 为什么不用传统爬虫？

1688 是典型的**动态渲染电商页面**，传统爬虫（Scrapy、requests + BeautifulSoup）面临的挑战：

| 挑战 | 传统爬虫 | browser-use + AI |
|------|---------|-----------------|
| JavaScript 动态渲染 | 无法执行 JS，拿不到真实 DOM | Playwright 运行完整浏览器，JS 正常执行 |
| 懒加载图片 | 需要模拟滚动，逻辑复杂 | AI 自主判断何时滚动、滚动多少 |
| 登录弹窗/验证码 | 需要针对性编写绕过逻辑 | AI "看到" 弹窗后自动点击关闭 |
| 页面结构变化 | CSS selector 失效就崩溃 | AI 通过视觉理解页面，不依赖固定 selector |
| 反爬检测 | 需要大量 headers/cookie 伪装 | 真实浏览器环境，指纹与正常用户一致 |

**核心思路：** 不再写"规则"告诉程序怎么爬，而是写"任务描述"让 AI 自己想办法完成。

### 4.2 技术选型与依赖关系

```
┌─────────────────────────────────────────────────────┐
│                    scrape.py                         │
│                  (爬取入口脚本)                        │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │             browser-use 框架                    │  │
│  │                                                │  │
│  │  ┌──────────────┐      ┌───────────────────┐   │  │
│  │  │    Agent      │      │     Browser       │   │  │
│  │  │  (任务循环)    │ ←──→ │  (浏览器控制)      │   │  │
│  │  └──────┬───────┘      └───────┬───────────┘   │  │
│  │         │                      │               │  │
│  │    ┌────▼────┐           ┌─────▼──────┐        │  │
│  │    │   LLM   │           │ Playwright  │        │  │
│  │    │ 接口层   │           │  Chromium   │        │  │
│  │    └────┬────┘           └────────────┘        │  │
│  │         │                                      │  │
│  └─────────┼──────────────────────────────────────┘  │
│            │                                         │
│  ┌─────────▼─────────────────────────────────────┐   │
│  │        ChatLiteLLMBedrock                      │   │
│  │      (自定义 LLM 适配器)                        │   │
│  │                                                │   │
│  │  LiteLLM → AWS Bedrock API → Claude Sonnet 4.5 │   │
│  │       (Bearer Token 认证)                       │   │
│  └────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

**三层组件：**

1. **Playwright** — 底层浏览器自动化引擎，负责打开页面、截图、执行点击/滚动等 DOM 操作
2. **browser-use Agent** — 中间层 AI Agent 循环框架，负责"观察→思考→行动"的决策循环
3. **Claude Sonnet (Bedrock)** — 顶层大脑，通过多模态能力"看"页面截图，决定下一步做什么

### 4.3 LLM 认证：Bedrock Bearer Token

#### 认证流程

```
.env 文件
  AWS_BEARER_TOKEN_BEDROCK=eyJhbGci...
  AWS_REGION=us-east-1
      │
      ▼
ChatLiteLLMBedrock（自定义适配器）
      │
      ▼ 调用 litellm.acompletion(model="bedrock/us.anthropic.claude-sonnet-4-5-...")
      │
      ▼
LiteLLM 内部处理：
  1. 检测到 model 前缀 "bedrock/" → 走 Bedrock 通道
  2. 读取环境变量 AWS_BEARER_TOKEN_BEDROCK
  3. 构建 HTTP 请求：
     - URL: https://bedrock-runtime.{region}.amazonaws.com/...
     - Headers: Authorization: Bearer {token}
     - Body: Claude 消息格式（含图片/文本）
      │
      ▼
AWS Bedrock API → Claude Sonnet 4.5
```

#### 为什么用 Bearer Token 而非标准 AWS SigV4？

标准 AWS 认证需要 Access Key + Secret Key + STS Session Token，配置复杂。Bearer Token 是一种简化的认证方式，适合：
- 内部代理/网关场景
- 临时令牌认证
- 不需要完整 IAM 配置的快速接入

LiteLLM 的处理逻辑（`litellm/llms/bedrock/base_aws_llm.py`）：

```python
# 如果检测到 Bearer Token，直接用简单的 HTTP 头认证
if aws_bearer_token:
    headers["Authorization"] = f"Bearer {aws_bearer_token}"
    headers["Content-Type"] = "application/json"
    # 不走 SigV4 签名流程
else:
    # 回退到标准 AWS SigV4 签名
    # 需要 access_key, secret_key, session_token 等
```

#### ChatLiteLLMBedrock 适配器详解

这个类继承自 browser-use 的 `BaseChatModel`，是连接 browser-use 框架与 AWS Bedrock 的桥梁：

```python
@dataclass
class ChatLiteLLMBedrock(BaseChatModel):
    model: str = "bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    max_tokens: int = 8192

    async def ainvoke(self, messages, output_format=None, **kwargs):
        # 1. 将 browser-use 内部消息格式 → OpenAI 消息格式
        openai_messages = OpenAIMessageSerializer.serialize_messages(messages)

        # 2. 如果需要结构化输出（output_format 不为 None）
        #    → 构建 tool_choice 强制 Claude 输出 JSON Schema
        if output_format is not None:
            params["tools"] = [{
                "type": "function",
                "function": {"name": "agent_output", "parameters": schema}
            }]
            params["tool_choice"] = {"type": "function", "function": {"name": "agent_output"}}

        # 3. 调用 LiteLLM（自动处理 Bedrock 认证）
        response = await litellm.acompletion(**params)

        # 4. 解析响应，提取文本或结构化数据
        # 5. 包装为 ChatInvokeCompletion 返回给 browser-use
```

**关键设计：**
- `max_tokens=8192`：爬取任务可能需要输出大量 URL，给足 token 空间
- 结构化输出通过 `tool_choice` 实现，确保 Claude 严格按 JSON Schema 返回
- 异常处理区分 `RateLimitError`（可重试）和一般错误

### 4.4 browser-use Agent 核心循环

#### Agent 创建参数

```python
agent = Agent(
    task=task,                    # 中文任务描述 Prompt
    llm=llm,                     # ChatLiteLLMBedrock 实例
    browser=browser,              # Playwright 浏览器实例
    max_actions_per_step=3,       # 每步最多执行 3 个浏览器动作
    use_vision=True,              # 启用多模态：Claude 会"看"页面截图
    vision_detail_level="low",    # 低分辨率截图（节省 token）
)
```

#### 单步执行流程（Agent.step()）

每一步包含 **4 个阶段**：

```
┌────────────────────────────────────────────────────────────┐
│                    Agent.step() 单步执行                     │
│                                                             │
│  阶段 0：预处理                                              │
│  ├─ 检查是否有验证码需要处理                                  │
│  └─ 处理上一步的遗留状态                                     │
│                                                             │
│  阶段 1：准备上下文                                          │
│  ├─ Playwright 截取当前页面截图（低分辨率）                    │
│  ├─ 提取页面 DOM 结构（元素树 + 可交互元素索引）               │
│  ├─ 收集历史动作记录                                         │
│  ├─ 检测是否有新的下载文件                                    │
│  ├─ 注入预算警告（如果接近 max_steps）                        │
│  └─ 组装完整消息：[系统 Prompt, 截图, DOM, 历史, 任务]        │
│                                                             │
│  阶段 2：LLM 推理 + 动作执行                                 │
│  ├─ 发送消息给 Claude（带超时，默认 90 秒）                   │
│  ├─ Claude 返回下一步动作（最多 3 个）                        │
│  ├─ 如果返回空动作 → 重试一次，仍然为空 → 回退为 done()       │
│  └─ 逐个执行动作（multi_act），带页面变化检测                  │
│                                                             │
│  阶段 3：后处理                                              │
│  ├─ 记录本步动作到历史                                       │
│  ├─ 更新执行计划状态                                         │
│  ├─ 统计连续失败次数                                         │
│  └─ 检测是否陷入循环（重复动作检测）                          │
└────────────────────────────────────────────────────────────┘
```

#### 主循环（Agent.run()）

```python
while n_steps <= max_steps:
    # 检查暂停/停止信号
    # 检查连续失败次数是否超限
    # 执行单步：step()
    # 如果 Agent 调用了 done() → 任务完成，跳出
    # 如果出错 → 记录错误，继续下一步
    # 如果达到 max_steps → 超时退出
# 返回 AgentHistoryList（包含所有步骤的截图、DOM、动作、结果）
```

#### Claude 可用的浏览器动作

browser-use 向 Claude 暴露以下动作，Claude 通过 tool_call 选择执行：

| 动作 | 参数 | 说明 | 特殊行为 |
|------|------|------|---------|
| `navigate` | url, new_tab | 导航到 URL | **终止序列**：后续动作取消 |
| `click_element` | index | 点击 DOM 元素 | 通过元素索引定位 |
| `input_text` | index, text | 向输入框填写文字 | — |
| `scroll` | direction, amount | 滚动页面 | 支持上下左右 |
| `send_keys` | keys | 发送键盘事件 | Enter, Escape 等 |
| `search_page` | pattern | 页面内文本搜索 | 支持正则 |
| `find_elements` | selector | CSS 选择器查找 | — |
| `extract` | text, schema | 提取结构化数据 | 带 LLM 辅助 |
| `screenshot` | — | 主动截图 | 仅 vision=auto 时可用 |
| `switch_tab` | tab_index | 切换标签页 | **终止序列** |
| `go_back` | — | 浏览器后退 | **终止序列** |
| `upload_file` | file_path, index | 上传文件 | — |
| `done` | success, text | 任务完成 | 必须是唯一动作 |

> **"终止序列"** 是什么意思？ 当 `max_actions_per_step=3` 时，Claude 可以一次返回 3 个动作。但如果其中一个是 `navigate` 或 `switch_tab` 这类会导致页面变化的动作，后续动作会被自动取消——因为页面已经变了，后续动作的目标 DOM 可能不存在了。

#### 页面变化检测机制

browser-use 有两层保护，防止在错误的页面上执行动作：

```
第 1 层（静态标记）：
  navigate/search/go_back/switch_tab 被标记为 terminates_sequence=True
  → 执行后直接跳过剩余动作

第 2 层（运行时检测）：
  每个动作执行后，对比执行前后的 URL + 当前聚焦元素
  → 如果发生变化 → 中止剩余动作队列
```

#### 连接断开重连

如果浏览器与 Agent 之间的连接断开（如 Chromium 崩溃）：

```
1. 捕获 ConnectionError
2. 等待重连事件（超时时间可配置）
3. 超时未重连 → 抛出 "connection lost" 错误
4. 重连成功 → 重试当前步骤
```

### 4.5 爬取任务 Prompt 详解

发送给 Claude 的任务描述是一段精心设计的中文 Prompt：

```python
task = f"""
你是一个图片采集助手。请完成以下任务：

1. 打开网页: {url}
2. 这是一个 1688 服装店铺页面，请找到商品列表区域
3. 如果页面有弹窗或登录提示，请关闭它们
4. 慢慢向下滚动页面，确保所有商品图片都加载出来
5. 找到页面中所有服装商品的主图（通常是商品列表中的大图），提取它们的图片 URL
6. 图片 URL 通常以 .jpg 或 .png 结尾，可能包含 cbu01.alicdn.com 等域名
7. 请把所有找到的商品图片 URL 汇总输出，每行一个 URL

注意：
- 只需要商品主图，不需要 logo、banner、广告图等
- 如果有分页，只需要采集第一页的商品图片
- 输出所有图片 URL 即可，后续下载由程序处理
"""
```

**Prompt 设计要点：**

| 设计 | 原因 |
|------|------|
| 步骤化指令（1-7） | 引导 AI 按正确顺序操作，避免遗漏 |
| 明确说"慢慢向下滚动" | 防止 AI 只滚动一次就认为加载完成 |
| 给出域名提示 `cbu01.alicdn.com` | 帮助 AI 识别哪些是商品图片 URL |
| "注意" 部分排除 logo/banner | 减少无效图片 |
| "只需要第一页" | 控制爬取范围，避免 Agent 步数不够 |
| "后续下载由程序处理" | 告诉 AI 不需要自己下载，只输出 URL |

### 4.6 图片 URL 提取

Claude Agent 完成任务后，返回的是一段包含 URL 的自然语言文本。需要用正则从中提取：

```python
def extract_image_urls(result) -> list[str]:
    urls = set()                   # set 自动去重
    text = str(result)             # 将 Agent 完整返回结果转为字符串

    # 三个正则，覆盖不同的 alicdn 子域名
    patterns = [
        r'https?://cbu\d+\.alicdn\.com/...',    # ① 1688 商品主图 CDN
        r'https?://img\.alicdn\.com/...',        # ② 阿里通用图片 CDN
        r'https?://[^\s"\'<>]+\.alicdn\.com/...', # ③ 兜底：任意 alicdn 子域
    ]
    for pattern in patterns:
        urls.update(re.findall(pattern, text, re.IGNORECASE))

    # 清理 URL 末尾粘连的标点
    return [u.rstrip(".,;)]}>'\"") for u in urls]
```

**为什么用正则而不是直接解析 Agent 输出？**

Claude 的输出格式不可控：
- 可能是整齐的每行一个 URL
- 可能是嵌在句子里："我找到了这些图片 https://cbu01... 和 https://cbu02..."
- 可能有 markdown 格式的链接 `[图片](https://...)`
- URL 末尾可能粘连了标点符号

用正则从全文中统一提取，然后去重 + 清理标点，是最稳健的方式。

**alicdn.com 域名体系：**

```
cbu01.alicdn.com  ← 1688 商品图片 CDN（China Business Unit）
cbu02.alicdn.com  ← 同上，不同节点
img.alicdn.com    ← 阿里通用图片 CDN（淘宝/天猫/1688 共用）
gw.alicdn.com     ← 全局网关图片
```

### 4.7 图片下载

提取到 URL 后，通过 httpx 异步客户端逐个下载：

```python
async def download_images(urls, save_dir, *, min_image_size=10240):
    async with httpx.AsyncClient(
        timeout=30,                  # 单张图片 30 秒超时
        follow_redirects=True,       # 跟随 CDN 302 跳转
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...",
            "Referer": "https://www.1688.com/",
        },
    ) as client:
        saved = 0
        for i, url in enumerate(urls, 1):
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    # 过滤小图（< 10KB）
                    if len(resp.content) < min_image_size:
                        continue
                    # 根据 Content-Type 决定扩展名
                    ct = resp.headers.get("content-type", "")
                    ext = ".png" if "png" in ct else ".webp" if "webp" in ct else ".jpg"
                    saved += 1
                    (save_dir / f"product_{saved:03d}{ext}").write_bytes(resp.content)
            except Exception as e:
                print(f"  下载出错: {e}")  # 单张失败不影响后续
```

**关键技术细节：**

| 机制 | 原理 |
|------|------|
| **Referer 头** | alicdn CDN 实施了**防盗链**策略。请求头中必须携带 `Referer: https://www.1688.com/`，否则返回 403 Forbidden。这模拟了"从 1688 页面点击图片"的合法来源 |
| **User-Agent** | 伪装为 Chrome 浏览器。部分 CDN 节点会拦截非浏览器的 UA（如 python-httpx） |
| **follow_redirects** | alicdn 经常做 302 重定向到实际存储节点（如从 cbu01 跳转到 cbu01-hz） |
| **10KB 过滤** | 商品主图通常 50KB~500KB。低于 10KB 的大概率是：logo (2-5KB)、icon (1-3KB)、1x1 像素跟踪图 (<1KB)、缩略图占位符 |
| **逐个下载** | 虽然用了 async，但是是顺序 `await`，没有并发。原因是避免短时间大量请求触发 CDN 限流/封 IP |
| **容错处理** | 每张图片独立 try-catch，单张下载失败（超时、404 等）不影响其他图片 |
| **编号跳跃** | `saved` 计数器只在成功保存时递增，所以文件编号是连续的（`product_001, 002, 003...`），被过滤的小图不占编号 |

### 4.8 完整爬取执行流程

```
$ .venv/bin/python -m clothworkflow.cli.scrape

┌──────────────────────────────────────────────────────────────────┐
│ 1. 解析命令行参数（或使用 config.yaml 默认值）                      │
│    -f taget_url.txt  -o downloaded_images  --max-steps 50        │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│ 2. 读取 URL 文件 → 得到 4 个店铺 URL                               │
└────────────────────────┬─────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│ 3. 创建 LLM 实例：ChatLiteLLMBedrock(model="bedrock/...claude...") │
│    └─ 内部通过 LiteLLM 读取 AWS_BEARER_TOKEN_BEDROCK 环境变量      │
└────────────────────────┬─────────────────────────────────────────┘
                         │
          ┌──────────────▼──────────────┐
          │    for url in urls:          │ ← 串行处理每个店铺
          │                              │
          │  ┌──────────────────────┐    │
          │  │ 4a. 提取店铺名       │    │
          │  │  URL → "qizhou888"   │    │
          │  │  创建输出目录         │    │
          │  └──────────┬───────────┘    │
          │             │                │
          │  ┌──────────▼───────────┐    │
          │  │ 4b. 启动 Chromium    │    │
          │  │  headless=false      │    │
          │  │  window=1280x800     │    │
          │  │  scale=1x            │    │
          │  └──────────┬───────────┘    │
          │             │                │
          │  ┌──────────▼───────────┐    │
          │  │ 4c. Agent 执行任务    │    │
          │  │  Step 1: navigate    │    │
          │  │  Step 2: 关闭弹窗    │    │
          │  │  Step 3~N: 滚动加载  │    │
          │  │  Step N+1: 提取 URL  │    │
          │  │  Step N+2: done()    │    │
          │  └──────────┬───────────┘    │
          │             │                │
          │  ┌──────────▼───────────┐    │
          │  │ 4d. 正则提取图片 URL  │    │
          │  │  alicdn.com 域名匹配  │    │
          │  │  set 去重             │    │
          │  └──────────┬───────────┘    │
          │             │                │
          │  ┌──────────▼───────────┐    │
          │  │ 4e. httpx 下载图片    │    │
          │  │  Referer 防盗链       │    │
          │  │  过滤 < 10KB 小图     │    │
          │  │  逐个保存 product_*   │    │
          │  └──────────┬───────────┘    │
          │             │                │
          │  ┌──────────▼───────────┐    │
          │  │ 4f. 关闭浏览器       │    │
          │  │  (finally 确保释放)   │    │
          │  └──────────────────────┘    │
          │                              │
          └──────────────┬───────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│ 5. 汇总统计                                                       │
│    shop2922242874804: 108 张                                      │
│    qizhou888: 130 张                                              │
│    总计: 433 张 | 保存位置: downloaded_images                      │
└──────────────────────────────────────────────────────────────────┘
```

### 4.9 一个真实爬取过程的 Step-by-Step 示例

以爬取 `https://qizhou888.1688.com/` 为例：

| Step | Claude 看到的页面 | Claude 的思考 | 执行的动作 |
|------|-----------------|-------------|-----------|
| 1 | 空白 about:blank 页 | "需要先打开目标 URL" | `navigate("https://qizhou888.1688.com/")` |
| 2 | 店铺首页 + 登录弹窗遮罩 | "有登录弹窗挡住了，需要关闭" | `click_element(关闭按钮 index)` |
| 3 | 店铺首页，显示前 20 个商品 | "需要向下滚动加载更多" | `scroll(down, 500)` |
| 4 | 加载出更多商品 | "继续滚动" | `scroll(down, 500)` × 3（max_actions_per_step=3） |
| 5-12 | 持续滚动，更多商品出现 | "还没到底部" | 持续 `scroll(down)` |
| 13 | 页面底部，"已经到底了" | "所有商品都加载了，现在提取图片 URL" | `extract(提取所有 img src)` |
| 14 | 获取到 DOM 中所有图片 URL | "任务完成" | `done(success=true, text="找到65张...")` |

**耗时估算：** 每步包含截图传输 + Claude 推理 + 动作执行，约 5-15 秒。一个店铺 15-30 步，总计 **3-8 分钟/店铺**。4 个店铺串行处理约 **15-30 分钟**。

### 4.10 错误处理机制

#### 店铺级别

```python
# scrape.py:142-150 — 单个店铺失败不影响后续
try:
    image_urls = await scrape_shop(...)
    all_results[shop_name] = image_urls or []
except Exception as e:
    print(f"爬取失败: {e}")
    all_results[shop_name] = []  # 记录为空，继续下一个店铺
```

#### Agent 级别（browser-use 内置）

```
1. LLM 超时重试：
   - Claude 推理超时（默认 90 秒）→ 重试一次
   - 仍然超时 → 该步骤标记为失败

2. 空动作处理：
   - Claude 返回空动作 → 发送提示消息要求重试
   - 重试后仍为空 → 自动回退为 done("failed") 安全退出

3. 连续失败检测：
   - 跟踪连续失败步数
   - 超过阈值 → 终止 Agent

4. 循环检测：
   - 检测到 Agent 在重复相同动作 → 注入提示引导改变策略

5. 导航失败处理：
   - 页面 DOM 为空 → 等 3 秒重检
   - 仍然为空 → 刷新页面，等 5 秒
   - 最终失败 → 返回 "可能是 JS 渲染/反爬/网络问题" 错误信息
```

#### 下载级别

```python
# 每张图片独立 try-catch
for url in urls:
    try:
        resp = await client.get(url)
        ...
    except Exception as e:
        print(f"下载出错: {e}")
        # 继续下一张，不中断
```

### 4.11 实操建议

| 场景 | 建议 |
|------|------|
| **首次运行** | 保持 `headless: false`，观察 Agent 操作过程，确认逻辑正确 |
| **页面复杂/商品多** | 调大 `max_steps`（如 80-100），给 Agent 更多步骤空间 |
| **节省成本** | 设置 `vision_detail_level: "low"`（已是默认），减少截图 token |
| **批量生产** | 设置 `headless: true`，不弹窗，服务器环境必选 |
| **添加新店铺** | 编辑 `clothworkflow/data/taget_url.txt`，每行一个 URL |
| **只爬某个店铺** | 创建新 URL 文件，用 `-f my_urls.txt` 指定 |
| **图片太小/太大** | 调整 `--min-size`，如 20480（20KB）过滤更严格 |
| **网络不稳定** | 下载超时默认 30 秒，个别失败会自动跳过 |

---

## 5. Step 2：AI 服装分析

### 5.1 分析原理

对每张商品图片，调用 **Gemini 2.5 Flash**（通过 OpenRouter）进行多模态分析，提取 **50+ 维度**的结构化服装特征。

```
商品图片（.jpg/.png）
    │
    ▼ base64 编码
    │
    ▼ 组装多模态消息（系统 Prompt + 图片 + 分析指令）
    │
    ▼ POST 请求 → OpenRouter API → Gemini 2.5 Flash
    │
    ▼ 返回 JSON 字符串
    │
    ▼ 解析为结构化 dict
    │
    ▼ 保存为 product_001.json
```

### 5.2 分析维度（50+ 字段）

Gemini 被要求按以下 JSON Schema 输出：

| 维度组 | 字段 | 示例值 |
|--------|------|--------|
| **basic_info** | category, subcategory, gender, age_range, season, occasion | 连衣裙, 吊带裙, 女, 18-30, [夏季], [约会, 派对] |
| **style** | primary_style, secondary_styles, aesthetic, trend_relevance | 甜美, [法式, 复古], Y2K, 高 |
| **colors** | primary_color, secondary_colors, color_scheme, temperature, saturation, personal_color | 粉色, [白色], 同色系, 暖色调, 中饱和, 春季型 |
| **material** | primary_fabric, blend, weight, texture, drape, elasticity, transparency, hand_feel | 雪纺, 涤纶混纺, 轻薄, 细腻, 好, 低, 微透, 顺滑 |
| **construction** | silhouette, fit, length, neckline, sleeve, waistline, hem, back_design, closure | A型, 修身, 及膝, V领, 无袖, 高腰, 荷叶边, 露背, 拉链 |
| **design_details** | pattern, decorations, pockets, stitching, craft, functional | 碎花, [蕾丝, 蝴蝶结], 无, 隐藏, [印花], [可调节肩带] |
| **visual_impression** | overall_feel, design_highlight, visual_weight | 浪漫优雅, 蝴蝶结装饰, 轻盈 |
| **body_compatibility** | suitable_body_types, flattering_features, size_range | [梨型, 沙漏型], [显腰细, 遮胯], S-XL |
| **commercial** | price_tier, target_audience, selling_points, similar_brands, coordination | 中等, 18-25岁女性, [显瘦, 百搭], [ZARA], [白色凉鞋] |
| **ecommerce** | title, keywords, hashtags, description | "法式碎花吊带连衣裙...", [碎花裙, 吊带裙], [#法式穿搭] |
| **image_info** | image_type, shown_colors, size_text, brand_visible | 平铺图, [粉色, 白色], 无, 否 |

### 5.3 图片编码

```python
def encode_image_base64(image_path):
    # 1. 根据扩展名确定 MIME 类型
    suffix = Path(image_path).suffix.lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp"}[suffix]

    # 2. 读取图片二进制 → base64 编码
    data = Path(image_path).read_bytes()
    b64 = base64.b64encode(data).decode()

    # 3. 构建 OpenAI 格式的 image_url
    return f"data:{mime};base64,{b64}", mime
```

### 5.4 API 调用

```python
# 组装请求
payload = {
    "model": "google/gemini-2.5-flash",
    "messages": [
        {"role": "system", "content": CLOTHING_ANALYSIS_PROMPT},   # 50+ 维度的分析指令
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": base64_image}},  # 图片
            {"type": "text", "text": "请分析这张服装图片"}                 # 指令
        ]}
    ],
    "max_tokens": 4096,
    "temperature": 0.1,    # 低温度 = 输出稳定、一致
}

# 发送请求
resp = httpx.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=120)
```

**为什么用 OpenRouter 而不直接调 Google API？**
- OpenRouter 提供统一的 OpenAI 兼容接口，切换模型只需改 model ID
- 支持多种支付方式，不需要 GCP 账号
- 自动处理 Gemini 的 base64 图片格式差异

### 5.5 响应解析与容错

```python
content = data["choices"][0]["message"]["content"]

# Gemini 有时会包裹 markdown 代码块
if content.startswith("```"):
    content = content.strip("`").removeprefix("json").strip()

try:
    result = json.loads(content)
except json.JSONDecodeError:
    # 解析失败时保留原始响应，标记 _parse_error
    result = {"raw_response": content, "_parse_error": True}
```

### 5.6 批量分析与增量模式

```bash
# 批量分析（自动跳过已分析的图片）
.venv/bin/python -m clothworkflow.cli.analyze \
    --dir downloaded_images --recursive --outdir analysis_results

# 强制重新分析所有图片
.venv/bin/python -m clothworkflow.cli.analyze \
    --dir downloaded_images --recursive --outdir analysis_results --force

# 只分析前 10 张（测试用）
.venv/bin/python -m clothworkflow.cli.analyze \
    --dir downloaded_images --recursive --outdir analysis_results --limit 10
```

**增量检测逻辑：** 对每张图片，检查输出目录中是否已存在同名 `.json` 文件。存在则跳过（除非 `--force`）。

**限流保护：** 批量分析时，每两次 API 调用之间间隔 `delay` 秒（默认 1.0 秒），避免触发 OpenRouter 速率限制。

### 5.7 输出格式

每张图片生成一个 JSON 文件，另外每个目录生成一个 `_summary.json` 汇总：

```
analysis_results/
├── qizhou888/
│   ├── product_001.json      ← 单张图片的 50+ 维度分析
│   ├── product_002.json
│   ├── ...
│   └── _summary.json         ← 汇总：总数/成功数/失败数
├── shop2922242874804/
│   └── ...
└── ...
```

单个 JSON 示例（节选）：

```json
{
  "basic_info": {
    "category": "连衣裙",
    "subcategory": "吊带连衣裙",
    "gender": "女",
    "age_range": "18-30",
    "season": ["夏季"],
    "occasion": ["约会", "度假", "日常"]
  },
  "style": {
    "primary_style": "甜美",
    "secondary_styles": ["法式", "度假风"],
    "aesthetic": "法式浪漫"
  },
  "colors": {
    "primary_color": "碎花多色",
    "secondary_colors": ["红色", "绿色"],
    "color_scheme": "撞色"
  },
  "_metadata": {
    "image": "downloaded_images/qizhou888/product_001.jpg",
    "model": "google/gemini-2.5-flash",
    "prompt_tokens": 1523,
    "completion_tokens": 876
  }
}
```

---

## 6. Step 3：索引构建

### 6.1 索引原理

将 432 条 JSON 分析结果转换为两种可检索的索引结构：

```
analysis/*.json
    │
    ├──→ text_builder.analysis_to_semantic_text()
    │        │
    │        ▼
    │    "这是一件女款连衣裙，细分品类吊带连衣裙。适合18-30岁。
    │     风格甜美，兼具法式、度假风。颜色碎花多色..."
    │        │
    │        ▼ BGE-M3 编码
    │    [0.023, -0.041, 0.089, ..., 0.015]  ← 1024 维向量
    │        │
    │        ▼ 保存
    │    _vector_index.npz   ← 向量矩阵 (N × 1024)
    │    _vector_meta.json   ← 元数据（图片路径、标题、类别等）
    │
    └──→ text_builder.analysis_to_bm25_tokens()
             │
             ▼
         ["连衣裙", "吊带", "甜美", "法式", "碎花", "夏季", ...]
             │
             ▼ 保存
         _bm25_corpus.json  ← BM25 分词语料库
```

### 6.2 语义文本生成

`text_builder.py` 将结构化 JSON 转为**自然语言段落**，作为 Embedding 的输入：

```python
def analysis_to_semantic_text(item) -> str:
    parts = []
    bi = item.get("basic_info", {})
    parts.append(f"这是一件{bi.get('gender','')}款{bi.get('category','')}，"
                 f"细分品类{bi.get('subcategory','')}。")

    style = item.get("style", {})
    parts.append(f"风格{style.get('primary_style','')}，"
                 f"兼具{'、'.join(style.get('secondary_styles',[]))}。")

    # ... 颜色、材质、版型、设计细节、视觉印象、体型适配、电商信息 ...
    return " ".join(parts)
```

**为什么不直接用 JSON 做 Embedding？** 自然语言段落比键值对有更强的语义信号。BGE-M3 是在自然语言文本上训练的，给它"这是一件甜美风格的碎花连衣裙"比给它 `{"primary_style": "甜美"}` 效果好得多。

### 6.3 BM25 分词

`analysis_to_bm25_tokens()` 从 JSON 中提取所有文本字段，用 jieba 分词：

```python
def analysis_to_bm25_tokens(item) -> list[str]:
    texts = []
    # 提取所有标量字段：category, primary_color, primary_style...
    # 提取所有列表字段：season, occasion, secondary_styles...
    raw = " ".join(texts)
    return tokenize_chinese(raw)
```

**jieba 服装领域定制：**

```python
# 添加服装专业词汇（防止被错误切分）
CUSTOM_WORDS = ["连衣裙", "半裙", "卫衣", "oversized", "显瘦",
                "水洗做旧", "Y2K", "美拉德", "多巴胺", ...]

# 停用词（过滤无意义的高频词）
STOP_WORDS = {"的", "了", "是", "有", "和", "在", "适合", ...}
```

例如"水洗做旧风格的oversized卫衣" → `["水洗做旧", "风格", "oversized", "卫衣"]`

如果不添加自定义词典，jieba 会把"水洗做旧"切成"水洗/做/旧"，把"连衣裙"切成"连衣/裙"。

### 6.4 向量编码

使用 BGE-M3 模型对语义文本做 Embedding：

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(ensure_bge_m3())
embeddings = model.encode(texts, normalize_embeddings=True)
# embeddings.shape = (432, 1024)
```

**normalize_embeddings=True**：归一化后，向量的余弦相似度 = 内积，计算更快。

### 6.5 增量检测

索引不是每次都重建。`indexer.py` 通过指纹检测判断是否需要更新：

```python
def get_analysis_fingerprint(analysis_dir):
    # 指纹 = 文件数量 + 最新修改时间
    files = list(analysis_dir.glob("**/*.json"))
    count = len([f for f in files if not f.name.startswith("_")])
    latest = max(f.stat().st_mtime for f in files)
    return f"{count}_{latest}"

def index_is_stale(analysis_dir):
    # 对比当前指纹与上次构建时的指纹
    saved = load_version_file()
    return saved["fingerprint"] != get_analysis_fingerprint(analysis_dir)
```

### 6.6 索引文件

| 文件 | 格式 | 内容 |
|------|------|------|
| `_vector_index.npz` | NumPy 压缩格式 | 432 × 1024 的 float32 向量矩阵 |
| `_vector_meta.json` | JSON 数组 | 每条记录的元数据：image, title, category, color, style, gender, semantic_text |
| `_bm25_corpus.json` | JSON 数组 | 每条记录的 jieba 分词列表 |
| `_index_version.json` | JSON 对象 | fingerprint, item_count, build_time（用于增量检测） |

---

## 7. Step 4：混合检索推荐

### 7.1 四阶段 Pipeline

这是整个系统最核心的检索架构。对用户输入的自然语言查询，经过 4 个阶段，最终输出 Top N 推荐：

```
用户查询: "显瘦的夏天裙子"
    │
    ▼ ────────── 阶段 1：BM25 关键词检索 ──────────
    │
    │  jieba 分词: ["显瘦", "夏天", "裙子"]
    │  BM25Okapi 评分: 对每条文档计算关键词匹配分数
    │  取 Top 15 (bm25_k=15)
    │  → 精确命中含"显瘦""裙子""夏天"的商品
    │
    ▼ ────────── 阶段 2：BGE-M3 语义向量检索 ──────────
    │
    │  BGE-M3 编码查询 → 1024 维向量
    │  与 432 条文档向量计算余弦相似度
    │  取 Top 15 (vector_k=15)
    │  → 语义理解: 显瘦 ≈ 修身/A型/高腰/深色
    │                夏天 ≈ 轻薄/无袖/透气
    │
    ▼ ────────── 阶段 3：RRF 融合排序 ──────────
    │
    │  合并两路结果（去重）
    │  RRF 公式: score(d) = Σ 1/(k + rank_i + 1)
    │    k=60（融合常数，越大越均匀）
    │    rank_i = 文档在第 i 路中的排名
    │  取 Top 20 (rerank_k=20)
    │
    ▼ ────────── 阶段 4：BGE-Reranker 精排 ──────────
    │
    │  输入: [(查询, 候选文档语义文本)] × 20 对
    │  BGE-Reranker-v2-M3 交叉编码器打分
    │  按分数重新排序
    │  取 Top 5 (top_n=5)
    │
    ▼
    最终推荐结果
```

### 7.2 阶段 1：BM25 关键词检索

**BM25 (Best Matching 25)** 是经典的信息检索算法，核心思想是**词频-逆文档频率**加权：

```
BM25(q, d) = Σ IDF(qi) × (tf(qi,d) × (k1+1)) / (tf(qi,d) + k1 × (1 - b + b × |d|/avgdl))
```

- `IDF(qi)`: 查询词 qi 的逆文档频率（越稀有的词权重越高）
- `tf(qi,d)`: 词 qi 在文档 d 中出现的次数
- `k1`, `b`: 参数（rank-bm25 库默认 k1=1.5, b=0.75）
- `|d|/avgdl`: 文档长度归一化

**实际效果：** 当用户查"显瘦的夏天裙子"：
- "裙子" → IDF 较低（很多商品都有），但匹配文档多
- "显瘦" → IDF 较高（只有部分商品描述中有），匹配精准
- 包含"显瘦"+"裙子"+"夏天"的商品得分最高

**局限：** BM25 只做字面匹配。"清凉" ≠ "夏天"，"修身" ≠ "显瘦"。需要语义检索补充。

### 7.3 阶段 2：BGE-M3 语义向量检索

**原理：** 将查询和文档都编码为向量，通过余弦相似度找语义相近的文档。

```python
# 编码查询
query_vec = model.encode([query], normalize_embeddings=True)

# 与所有文档向量计算余弦相似度（归一化后 = 内积）
scores = embeddings @ query_vec.T  # (432,1024) × (1024,1) = (432,1)

# 取 Top K
top_indices = np.argsort(scores.flatten())[::-1][:vector_k]
```

**BGE-M3 的优势：**
- 支持 8192 token 长文本
- 多语言（中英文都好）
- 1024 维度，表达能力强
- 专为检索任务优化（区分 query 和 passage）

**语义匹配示例：**
| 查询 | 字面无关但语义相关的匹配 |
|------|----------------------|
| "显瘦" | 修身、A 型廓形、高腰、深色系、竖条纹 |
| "夏天" | 轻薄面料、无袖、透气、清凉、雪纺 |
| "参加派对" | 亮片装饰、深V领、修身、高级感 |
| "通勤穿" | 商务休闲、纯色、衬衫、直筒裤 |

### 7.4 阶段 3：RRF 融合

**问题：** BM25 和向量检索各有优势，如何合并？

**Reciprocal Rank Fusion (RRF)** 是一种简单有效的排名融合方法：

```python
def rrf_score(doc, rankings, k=60):
    score = 0
    for ranking in rankings:
        if doc in ranking:
            rank = ranking.index(doc)
            score += 1.0 / (k + rank + 1)
    return score
```

**直觉：** 一个文档如果在多路检索中排名都靠前，融合分数就高。

**k=60 的作用：** k 越大，各路排名差异的影响越小（更"民主"）；k 越小，头部排名的优势越大。

**示例：**
| 文档 | BM25 排名 | 向量排名 | RRF 分数 |
|------|----------|---------|---------|
| 商品 A | 1 | 3 | 1/62 + 1/64 = 0.0317 |
| 商品 B | 5 | 1 | 1/66 + 1/62 = 0.0313 |
| 商品 C | 2 | 10 | 1/63 + 1/71 = 0.0300 |
| 商品 D | 不在 | 2 | 0 + 1/63 = 0.0159 |

→ 排序：A > B > C > D（在两路都靠前的 A 赢了只在一路靠前的 D）

### 7.5 阶段 4：BGE-Reranker 精排

**为什么还需要精排？** 前三阶段的模型都是 **双塔模型（Bi-Encoder）**——查询和文档分别编码，再算相似度。效率高但精度有限。

Reranker 是 **交叉编码器（Cross-Encoder）**——查询和文档拼接后一起输入模型，能捕捉更细粒度的语义交互：

```
Bi-Encoder（快但粗）：
  encode("显瘦的夏天裙子") → vec_q
  encode("这是一件A型高腰连衣裙...") → vec_d
  score = cosine(vec_q, vec_d)

Cross-Encoder（慢但精）：
  score = model("显瘦的夏天裙子 [SEP] 这是一件A型高腰连衣裙...")
  → 模型能注意到"显瘦"与"A型高腰"的直接关联
```

**为什么不全用 Cross-Encoder？** 432 条文档全部做交叉编码太慢。所以先用快速的 BM25 + 向量检索缩小到 20 条候选，再用 Reranker 精排。

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder(ensure_reranker())
pairs = [(query, candidate["semantic_text"]) for candidate in candidates]
scores = reranker.predict(pairs)
# 按 scores 降序排列，取 Top N
```

### 7.6 输出结果结构

```json
{
  "query": "显瘦的夏天裙子",
  "query_tokens": ["显瘦", "夏天", "裙子"],
  "total_items": 432,
  "candidates_before_rerank": 20,
  "timing": {
    "bm25_ms": 2.1,
    "vector_ms": 5.3,
    "merge_ms": 0.4,
    "rerank_ms": 120.5,
    "total_ms": 128.3
  },
  "results": [
    {
      "rank": 1,
      "title": "夏季高腰A型碎花连衣裙",
      "category": "连衣裙",
      "color": "碎花多色",
      "style": "甜美",
      "gender": "女",
      "image": "downloaded_images/qizhou888/product_015.jpg",
      "scores": {
        "reranker": 0.923,
        "vector_sim": 0.847,
        "bm25": 12.34,
        "rrf": 0.0317,
        "source": "both"
      }
    }
  ]
}
```

### 7.7 参数调优建议

| 参数 | 默认值 | 调大效果 | 调小效果 |
|------|-------|---------|---------|
| `bm25_k` | 15 | 更多关键词候选，召回率↑ 但噪音↑ | 更精确但可能漏掉 |
| `vector_k` | 15 | 更多语义候选 | 同上 |
| `rerank_k` | 20 | 精排考虑更多候选，质量↑ 但速度↓ | 更快但可能漏掉好结果 |
| `rrf_k` | 60 | 排名差异影响更小，更"均匀" | 头部排名优势更大 |
| `top_n` | 5 | 返回更多结果 | 只要最好的几个 |

---

## 8. Web 界面与 API

### 8.1 架构

```
┌────────────────────────┐          ┌───────────────────────────┐
│   React 前端            │          │   FastAPI 后端             │
│   (Vite + Ant Design)   │  HTTP    │   (端口 8000)              │
│                         │ ──────→  │                           │
│   /search  智能搜索      │          │   /api/search   混合检索   │
│   /stats   数据概览      │          │   /api/stats    统计数据   │
│   /config  配置管理      │          │   /api/image    图片服务   │
│   /about   项目介绍      │          │   /api/config   配置读写   │
│                         │          │   /api/load     加载数据   │
│   构建产物:              │          │   /api/product  商品详情   │
│   web/dist/             │          │   /api/status   状态查询   │
└────────────────────────┘          └───────────────────────────┘
```

**部署模式：** FastAPI 自动挂载 `web/dist/` 静态资源，前后端合并为一个进程。访问 `http://localhost:8000` 即可使用完整界面。

### 8.2 API 端点详解

| 端点 | 方法 | 用途 | 参数 |
|------|------|------|------|
| `/api/analysis-dirs` | GET | 列出可用的分析数据目录 | — |
| `/api/load` | POST | 加载指定分析数据 + 自动构建索引 | `{"analysis_dir": "path"}` |
| `/api/search` | POST | 执行混合检索 | `{"query": "显瘦裙子", "top_n": 5}` |
| `/api/image` | GET | 返回商品图片 | `?path=downloaded_images/xxx.jpg` |
| `/api/product/{stem}` | GET | 返回完整分析 JSON | stem = product_001 |
| `/api/stats` | GET | 返回分类分布统计 | — |
| `/api/config` | GET | 返回当前配置 + YAML 原文 | — |
| `/api/config` | PUT | 保存修改后的 YAML 配置 | `{"yaml_content": "..."}` |
| `/api/status` | GET | 返回检索器状态 | — |

### 8.3 图片路径解析

API 中有一个重要的辅助函数 `resolve_image_path()`，因为分析 JSON 中的图片路径可能是各种格式：

```python
def resolve_image_path(image_path):
    # 依次尝试 5 种路径解析策略：
    # 1. 绝对路径直接检查
    # 2. 相对于项目根目录
    # 3. 相对于 downloaded_images/
    # 4. 在 downloaded_images/ 子目录中搜索
    # 5. 两级深度搜索（downloaded_images/shop/product.jpg）
```

### 8.4 启动方式

```bash
# 生产模式（使用预构建的前端）
.venv/bin/python -m clothworkflow.api
# → http://localhost:8000

# 前端开发模式（热更新）
cd clothworkflow/web
npm install && npm run dev
# → http://localhost:5173（自动代理 API 到 8000 端口）
```

### 8.5 自动初始化

API 启动时会自动：
1. 扫描可用的分析数据目录（analysis/, testbed/analysis/ 等）
2. 加载第一个找到的数据集
3. 检测索引是否过期，需要时自动重建
4. 挂载前端静态资源（如果 `web/dist/` 存在）

---

## 9. 常见问题与排障

### 9.1 爬取相关

**Q: 爬取时 Claude 一直在循环滚动，不停止？**
A: 调大 `max_steps`（如 80），并检查页面是否有无限滚动。如果店铺商品特别多，可以在 Prompt 中加"只采集前 100 个商品"。

**Q: 爬取到的图片很少 / 都是小图？**
A: 检查 `min_image_size` 设置是否过大。可以先设为 0 查看所有图片大小分布，再决定过滤阈值。

**Q: 下载图片时返回 403？**
A: alicdn CDN 需要正确的 Referer 头。检查代码中是否设置了 `Referer: https://www.1688.com/`。如果换了其他平台，需要修改 Referer。

**Q: AWS_BEARER_TOKEN_BEDROCK 怎么获取？**
A: 这取决于你的 AWS 环境配置。如果通过内部代理/网关访问 Bedrock，令牌由网关签发。标准 AWS 用户可以改用 Access Key + Secret Key 认证（去掉 Bearer Token 环境变量，设置 `AWS_ACCESS_KEY_ID` 和 `AWS_SECRET_ACCESS_KEY`）。

### 9.2 分析相关

**Q: Gemini 返回的 JSON 解析失败？**
A: 偶尔发生，系统会自动保存原始响应并标记 `_parse_error: true`。可以用 `--force` 重新分析那些失败的图片。

**Q: 分析速度太慢？**
A: 默认每次请求间隔 1 秒（避免限流）。如果 OpenRouter 配额充足，可以减小 `delay` 到 0.3 秒。

### 9.3 检索相关

**Q: 首次运行下载 BGE 模型很慢？**
A: BGE-M3 约 2.2GB，BGE-Reranker 约 1.1GB。可以手动下载后设置 `BGE_M3_PATH` 和 `BGE_RERANKER_PATH` 环境变量指向本地路径。

**Q: 搜索结果不太相关？**
A: 尝试：
1. 使用更具体的查询："夏天显瘦的黑色A字裙" 比 "裙子" 效果好
2. 调大 `rerank_k`（如 30），让 Reranker 考虑更多候选
3. 检查分析 JSON 的质量——如果 `_parse_error: true` 的文档多，会影响索引质量

### 9.4 快速验证

如果只想快速体验推荐功能，无需任何 API 密钥：

```bash
# 使用预置的 testbed 数据
.venv/bin/python -m clothworkflow.cli.recommend \
    --analysis-dir clothworkflow/testbed/analysis \
    --query "参加派对穿的裙子"

# 或启动 Web 界面
.venv/bin/python -m clothworkflow.api
```

项目已包含 432 条预分析数据和预构建索引，开箱即用。
