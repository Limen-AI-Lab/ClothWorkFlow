"""模型管理：本地缺失时自动从 HuggingFace 下载"""

from pathlib import Path

from .config import BGE_M3_PATH, RERANKER_PATH

# HuggingFace 模型 ID
_BGE_M3_REPO = "BAAI/bge-m3"
_RERANKER_REPO = "BAAI/bge-reranker-v2-m3"


def _has_embedding_weights(p: Path) -> bool:
    """sentence-transformers 需要至少一份权重，仅有 config.json 的半成品目录无效"""
    if (p / "model.safetensors").exists() or (p / "pytorch_model.bin").exists():
        return True
    if any(p.glob("model-*.safetensors")):
        return True
    if any(p.glob("*.safetensors")):
        return True
    return False


def _is_valid_model_dir(path: str) -> bool:
    """目录存在且含 config.json 与可用权重"""
    p = Path(path)
    return (
        p.is_dir()
        and (p / "config.json").exists()
        and _has_embedding_weights(p)
    )


def _is_valid_reranker_dir(path: str) -> bool:
    """CrossEncoder 同样需要权重文件"""
    p = Path(path)
    if not p.is_dir() or not (p / "config.json").exists():
        return False
    return _has_embedding_weights(p)


def _download_model(repo_id: str, local_dir: str) -> str:
    """从 HuggingFace 下载模型到指定目录"""
    from huggingface_hub import snapshot_download

    print(f"  本地未找到模型，正在从 HuggingFace 下载 {repo_id} ...")
    path = snapshot_download(repo_id=repo_id, local_dir=local_dir)
    print(f"  下载完成: {path}")
    return path


def ensure_bge_m3() -> str:
    """确保 BGE-M3 模型可用，返回模型路径"""
    if _is_valid_model_dir(BGE_M3_PATH):
        return BGE_M3_PATH
    # 下载到项目内 models/ 目录
    from .config import PROJECT_ROOT
    local_dir = str(PROJECT_ROOT / "models" / "bge-m3")
    if _is_valid_model_dir(local_dir):
        return local_dir
    return _download_model(_BGE_M3_REPO, local_dir)


def ensure_reranker() -> str:
    """确保 BGE-Reranker 模型可用，返回模型路径"""
    if _is_valid_reranker_dir(RERANKER_PATH):
        return RERANKER_PATH
    from .config import PROJECT_ROOT
    local_dir = str(PROJECT_ROOT / "models" / "bge-reranker-v2-m3")
    if _is_valid_reranker_dir(local_dir):
        return local_dir
    return _download_model(_RERANKER_REPO, local_dir)
