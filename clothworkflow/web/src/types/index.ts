// API 响应类型定义

export interface StatusResponse {
  loaded: boolean
  count: number
  analysis_dir: string
}

export interface AnalysisDir {
  path: string
  label: string
  type: string
}

export interface AnalysisDirsResponse {
  dirs: AnalysisDir[]
}

export interface LoadRequest {
  analysis_dir: string
}

export interface LoadResponse {
  status: string
  count: number
}

export interface SearchRequest {
  query: string
  top_n?: number
}

export interface SearchScore {
  reranker: number
  vector_sim: number
  bm25: number
  rrf: number
  source: string
}

export interface SearchResult {
  rank: number
  title: string
  category: string
  primary_color: string
  primary_style: string
  gender: string
  image_url: string
  scores: SearchScore
}

export interface SearchTiming {
  bm25_ms: number
  vector_ms: number
  rerank_ms: number
  total_ms: number
}

export interface SearchResponse {
  query: string
  query_tokens: string[]
  total_items: number
  candidates: number
  timing: SearchTiming
  results: SearchResult[]
}

export interface ProductResponse {
  [key: string]: any // 完整的产品分析数据，包含 50+ 维度
}

export interface StatsResponse {
  [key: string]: any // 统计分布数据
}

export interface ConfigResponse {
  yaml: string
  current: Record<string, any>
}

export interface ConfigUpdateRequest {
  yaml: string
}
