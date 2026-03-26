import axios from 'axios'
import type {
  StatusResponse,
  AnalysisDirsResponse,
  LoadRequest,
  LoadResponse,
  SearchRequest,
  SearchResponse,
  ProductResponse,
  StatsResponse,
  ConfigResponse,
  ConfigUpdateRequest,
} from './types'

const api = axios.create({
  baseURL: '',  // uses vite proxy in dev, same origin in production
  timeout: 120000,
})

// 状态查询
export const getStatus = async (): Promise<StatusResponse> => {
  const { data } = await api.get('/api/status')
  return data
}

// 获取分析目录列表
export const getAnalysisDirs = async (): Promise<AnalysisDirsResponse> => {
  const { data } = await api.get('/api/analysis-dirs')
  return data
}

// 加载数据
export const loadData = async (request: LoadRequest): Promise<LoadResponse> => {
  const { data } = await api.post('/api/load', request)
  return data
}

// 搜索商品
export const searchProducts = async (
  request: SearchRequest
): Promise<SearchResponse> => {
  const { data } = await api.post('/api/search', request)
  return data
}

// 获取图片 URL
// image_url 来自后端，已经是 /api/image?path=xxx 格式
// 使用相对路径，通过 vite proxy 在开发环境工作，生产环境使用同源
export const getImageUrl = (imageUrl: string): string => {
  if (!imageUrl) return ''
  if (imageUrl.startsWith('http')) return imageUrl
  return imageUrl  // relative path, works with proxy
}

// 获取商品详情
export const getProduct = async (stem: string): Promise<ProductResponse> => {
  const { data } = await api.get(`/api/product/${stem}`)
  return data
}

// 获取统计数据
export const getStats = async (): Promise<StatsResponse> => {
  const { data } = await api.get('/api/stats')
  return data
}

// 获取配置
export const getConfig = async (): Promise<ConfigResponse> => {
  const { data } = await api.get('/api/config')
  return data
}

// 更新配置
export const updateConfig = async (
  request: ConfigUpdateRequest
): Promise<{ status: string }> => {
  const { data } = await api.put('/api/config', request)
  return data
}

export default api
