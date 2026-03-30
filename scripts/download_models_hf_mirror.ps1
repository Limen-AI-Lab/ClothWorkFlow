# Download BGE-M3 + bge-reranker-v2-m3 using hf-mirror.com (when huggingface.co is blocked or Git LFS xet fails).
# Requires: git, git-lfs, curl.exe
# Run from repo root:  powershell -ExecutionPolicy Bypass -File scripts\download_models_hf_mirror.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path (Join-Path $Root "pyproject.toml"))) {
    Write-Error "Run from ClothWorkFlow repo (pyproject.toml not found above scripts/)."
}
$Models = Join-Path $Root "models"
New-Item -ItemType Directory -Force -Path $Models | Out-Null

function Clone-NoLfs {
    param([string]$Url, [string]$Dest)
    if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
    $env:GIT_LFS_SKIP_SMUDGE = "1"
    try { git clone $Url $Dest }
    finally { Remove-Item Env:GIT_LFS_SKIP_SMUDGE -ErrorAction SilentlyContinue }
}

Write-Host "==> bge-m3"
Clone-NoLfs "https://hf-mirror.com/BAAI/bge-m3" (Join-Path $Models "bge-m3")
$b = Join-Path $Models "bge-m3"
curl.exe -L --connect-timeout 120 --retry 3 --retry-delay 5 -o "$b\pytorch_model.bin" "https://hf-mirror.com/BAAI/bge-m3/resolve/main/pytorch_model.bin"
curl.exe -L --connect-timeout 120 -o "$b\colbert_linear.pt" "https://hf-mirror.com/BAAI/bge-m3/resolve/main/colbert_linear.pt"
curl.exe -L --connect-timeout 120 -o "$b\sparse_linear.pt" "https://hf-mirror.com/BAAI/bge-m3/resolve/main/sparse_linear.pt"
curl.exe -L --connect-timeout 120 -o "$b\tokenizer.json" "https://hf-mirror.com/BAAI/bge-m3/resolve/main/tokenizer.json"
curl.exe -L --connect-timeout 120 -o "$b\sentencepiece.bpe.model" "https://hf-mirror.com/BAAI/bge-m3/resolve/main/sentencepiece.bpe.model"

Write-Host "==> bge-reranker-v2-m3"
Clone-NoLfs "https://hf-mirror.com/BAAI/bge-reranker-v2-m3" (Join-Path $Models "bge-reranker-v2-m3")
$r = Join-Path $Models "bge-reranker-v2-m3"
curl.exe -L --connect-timeout 120 --retry 3 --retry-delay 5 -o "$r\model.safetensors" "https://hf-mirror.com/BAAI/bge-reranker-v2-m3/resolve/main/model.safetensors"
curl.exe -L --connect-timeout 120 -o "$r\sentencepiece.bpe.model" "https://hf-mirror.com/BAAI/bge-reranker-v2-m3/resolve/main/sentencepiece.bpe.model"
curl.exe -L --connect-timeout 120 -o "$r\tokenizer.json" "https://hf-mirror.com/BAAI/bge-reranker-v2-m3/resolve/main/tokenizer.json"

Write-Host "Done. Models under: $Models"
