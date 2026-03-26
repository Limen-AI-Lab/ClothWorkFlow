# ClothWorkFlow

服装图片爬取 + AI 特征分析 + 混合检索智能推荐

## 项目结构

```
ClothWorkFlow/
├── clothworkflow/                  # 主包
│   ├── core/                       # 核心逻辑
│   │   ├── config.py               #   统一配置（路径/API/模型/默认参数）
│   │   ├── analyzer.py             #   Gemini 多模态分析（50+维度 Prompt）
│   │   ├── text_builder.py         #   语义文本生成 + jieba 中文分词
│   │   ├── indexer.py              #   向量索引 + BM25 语料构建
│   │   ├── retriever.py            #   混合检索 + Reranker 精排
│   │   └── llm_bedrock.py          #   AWS Bedrock LLM 适配器
│   │
│   ├── cli/                        # CLI 入口
│   │   ├── scrape.py               #   爬取 1688 店铺图片
│   │   ├── analyze.py              #   批量分析服装特征
│   │   ├── recommend.py            #   智能推荐检索
│   │   └── pipeline.py             #   一键全流程
│   │
│   ├── data/                       # 输入数据
│   │   └── taget_url.txt           #   目标店铺 URL 列表
│   │
│   └── testbed/                    # 测试材料
│       ├── images/                 #   12张测试图片（4店铺各3张）
│       └── analysis/               #   分析结果 + 向量索引
│
├── downloaded_images/              # 爬取的全量图片（gitignore）
├── pyproject.toml
├── .env / .gitignore / README.md
```

## 环境准备

```bash
# 1. 安装依赖
uv sync                                     # 安装核心依赖
uv sync --extra scrape                       # 如需爬取
uv run playwright install chromium           # 如需爬取

# 2. 配置环境变量（复制 .env.example 为 .env 并填写）
cp .env.example .env

# 或直接导出环境变量：
export OPENROUTER_API_KEY="your-key"         # 分析必需
export AWS_BEARER_TOKEN_BEDROCK="your-token" # 爬取必需
export AWS_REGION="us-east-1"                # 爬取必需
```

## 使用方式

### 方式一：python -m 模块调用

```bash
# 分析
.venv/bin/python -m clothworkflow.cli.analyze --dir downloaded_images --recursive --outdir analysis_results

# 建索引 + 推荐
.venv/bin/python -m clothworkflow.cli.recommend --analysis-dir analysis_results --build-index
.venv/bin/python -m clothworkflow.cli.recommend --analysis-dir analysis_results --query "显瘦的裙子"
.venv/bin/python -m clothworkflow.cli.recommend --analysis-dir analysis_results  # 交互模式

# 一键全流程
.venv/bin/python -m clothworkflow.cli.pipeline --images downloaded_images --analysis analysis_results

# 爬取
.venv/bin/python -m clothworkflow.cli.scrape
```

### 方式二：用 testbed 快速体验

```bash
# 直接用预置的 testbed 数据测试推荐
.venv/bin/python -m clothworkflow.cli.recommend \
    --analysis-dir clothworkflow/testbed/analysis \
    --query "参加派对穿的裙子"
```

## 推荐架构

```
用户: "显瘦的夏天裙子"
  ├─ jieba 分词: 显瘦 / 夏天 / 裙子
  ├─ BM25 关键词检索 → 精确命中含"显瘦""裙子"的商品
  ├─ BGE-M3 语义检索 → 理解 显瘦≈修身/A型/高腰/深色
  ├─ RRF 融合排序
  └─ BGE-Reranker 精排 → Top N 推荐
```

## 本地模型

- **BGE-M3** — embedding（1024维）
- **BGE-Reranker-v2-M3** — 交叉编码器精排

**自动下载**：首次运行时，模型会从 HuggingFace 自动下载（需科学上网）。

**手动指定**：如已下载模型，可设置环境变量或修改 `config.yaml`：
```bash
export BGE_M3_PATH="/your/path/to/bge-m3"
export BGE_RERANKER_PATH="/your/path/to/bge-reranker-v2-m3"
```
