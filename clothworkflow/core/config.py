"""
统一配置管理

优先级：环境变量 > config.yaml > 代码默认值
"""

import os
from pathlib import Path

# ============ 项目路径 ============
PACKAGE_ROOT = Path(__file__).parent.parent       # clothworkflow/
PROJECT_ROOT = PACKAGE_ROOT.parent                # ClothWorkFlow/
CONFIG_FILE = PROJECT_ROOT / "config.yaml"

# ============ 加载 YAML 配置 ============

def _load_yaml() -> dict:
    """加载 config.yaml，不存在则返回空字典"""
    if not CONFIG_FILE.exists():
        return {}
    try:
        import yaml
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # 没装 pyyaml 则手动解析简单 YAML
        return _parse_simple_yaml(CONFIG_FILE)


def _parse_simple_yaml(path: Path) -> dict:
    """简易 YAML 解析（仅支持两层嵌套 + 字符串/数字/布尔值）"""
    result = {}
    current_section = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" ") and stripped.endswith(":"):
            current_section = stripped[:-1]
            result[current_section] = {}
        elif current_section and ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            # 去掉行内注释
            if " #" in val:
                val = val[:val.index(" #")].strip().strip('"').strip("'")
            # 类型转换
            if val.lower() == "true":
                val = True
            elif val.lower() == "false":
                val = False
            elif val == "":
                val = ""
            else:
                try:
                    val = int(val)
                except ValueError:
                    try:
                        val = float(val)
                    except ValueError:
                        pass
            result[current_section][key] = val
    return result


_CFG = _load_yaml()


def _get(section: str, key: str, env_var: str | None = None, default=None):
    """读取配置值，优先级：环境变量 > YAML > 默认值"""
    if env_var:
        env_val = os.getenv(env_var)
        if env_val:
            return env_val
    yaml_val = _CFG.get(section, {}).get(key)
    if yaml_val is not None and yaml_val != "":
        return yaml_val
    return default


# ============ API 密钥 ============
OPENROUTER_API_KEY = _get("api", "openrouter_api_key", "OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = _get("api", "openrouter_api_url", default="https://openrouter.ai/api/v1/chat/completions")
AWS_BEARER_TOKEN = _get("api", "aws_bearer_token", "AWS_BEARER_TOKEN_BEDROCK", "")
AWS_REGION = _get("api", "aws_region", "AWS_REGION", "us-east-1")

# ============ 模型配置 ============
DEFAULT_ANALYSIS_MODEL = _get("models", "analysis_model", default="google/gemini-2.5-flash")
DEFAULT_BEDROCK_MODEL = _get("models", "bedrock_model", default="bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0")
BGE_M3_PATH = str(_get("models", "bge_m3_path", "BGE_M3_PATH", "BAAI/bge-m3"))
RERANKER_PATH = str(_get("models", "bge_reranker_path", "BGE_RERANKER_PATH", "BAAI/bge-reranker-v2-m3"))

# ============ 路径配置 ============
def _resolve_path(val, default: Path) -> Path:
    if val and val != default:
        p = Path(str(val))
        return p if p.is_absolute() else PROJECT_ROOT / p
    return default

DEFAULT_URL_FILE = _resolve_path(_get("paths", "url_file"), PACKAGE_ROOT / "data" / "taget_url.txt")
DEFAULT_DOWNLOAD_DIR = _resolve_path(_get("paths", "download_dir"), PROJECT_ROOT / "downloaded_images")
DEFAULT_ANALYSIS_DIR = _resolve_path(_get("paths", "analysis_dir"), PROJECT_ROOT / "analysis_results")
TESTBED_DIR = _resolve_path(_get("paths", "testbed_dir"), PACKAGE_ROOT / "testbed")
TESTBED_IMAGES_DIR = TESTBED_DIR / "images"
TESTBED_ANALYSIS_DIR = TESTBED_DIR / "analysis"

# ============ 爬取参数 ============
SCRAPE_MAX_STEPS = int(_get("scrape", "max_steps", default=50))
SCRAPE_MIN_IMAGE_SIZE = int(_get("scrape", "min_image_size", default=10240))
SCRAPE_HEADLESS = bool(_get("scrape", "headless", default=False))

# ============ 分析参数 ============
ANALYZE_TIMEOUT = int(_get("analyze", "timeout", default=120))
ANALYZE_DELAY = float(_get("analyze", "delay", default=1.0))
ANALYZE_MAX_TOKENS = int(_get("analyze", "max_tokens", default=4096))
ANALYZE_TEMPERATURE = float(_get("analyze", "temperature", default=0.1))

# ============ 推荐参数 ============
RECOMMEND_TOP_N = int(_get("recommend", "top_n", default=5))
RECOMMEND_BM25_K = int(_get("recommend", "bm25_k", default=15))
RECOMMEND_VECTOR_K = int(_get("recommend", "vector_k", default=15))
RECOMMEND_RERANK_K = int(_get("recommend", "rerank_k", default=20))
RECOMMEND_RRF_K = int(_get("recommend", "rrf_k", default=60))

# ============ 索引文件名 ============
INDEX_VECTOR_FILE = _get("index", "vector_file", default="_vector_index.npz")
INDEX_META_FILE = _get("index", "meta_file", default="_vector_meta.json")
INDEX_BM25_FILE = _get("index", "bm25_file", default="_bm25_corpus.json")
INDEX_VERSION_FILE = _get("index", "version_file", default="_index_version.json")
