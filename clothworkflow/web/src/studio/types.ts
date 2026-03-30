/** Aligned with ai-studio reference (Downloads/ai-studio/types.ts) */

export interface UploadedImage {
  id: string
  file: File
  previewUrl: string
  base64Data: string
  mimeType: string
}

/** 浏览器 IndexedDB 中保存的预设模特（不含 File，仅元数据 + base64） */
export interface ModelPreset {
  id: string
  name: string
  createdAt: number
  mimeType: string
  base64Data: string
}

export interface GenerationConfig {
  clothes: UploadedImage[]
  model: UploadedImage | null
  scene: UploadedImage | null
  style: string
  aspectRatio: '1:1' | '3:4' | '4:3' | '16:9' | '9:16'
  pose?: string
  environment?: string
  additionalPrompt?: string
}

export type PhotoStyle = {
  id: string
  name: string
  description: string
  promptModifier: string
}

export const PHOTO_STYLES: PhotoStyle[] = [
  {
    id: 'studio-minimal',
    name: '极简摄影棚',
    description: '干净的背景，柔和的灯光，专注于细节。',
    promptModifier:
      'High-end studio photography, clean minimalist aesthetic, softbox lighting, 8k resolution, sharp focus on fabric texture.',
  },
  {
    id: 'street-chic',
    name: '街头时尚',
    description: '自然抓拍，城市环境，自然日光。',
    promptModifier:
      'Street fashion photography, urban candid style, natural sunlight, bokeh background, dynamic pose, vogue magazine style.',
  },
  {
    id: 'cinematic-mood',
    name: '电影质感',
    description: '戏剧性布光，电影调色，氛围感强。',
    promptModifier:
      'Cinematic lighting, moody atmosphere, teal and orange color grading, dramatic shadows, film grain, highly detailed.',
  },
  {
    id: 'editorial-luxury',
    name: '奢华大片',
    description: '高级时尚，前卫构图，艺术感强。',
    promptModifier:
      'High fashion editorial, luxury lifestyle, avant-garde composition, perfect lighting, glossy magazine finish.',
  },
]

export const ENVIRONMENTS = [
  {
    id: 'default',
    name: '使用上传的场景图 / 默认',
    prompt: 'neutral studio background',
  },
  {
    id: 'cafe',
    name: '精致咖啡馆',
    prompt:
      'chic modern cafe interior with warm ambient lighting, coffee shop atmosphere',
  },
  {
    id: 'urban',
    name: '繁华都市',
    prompt: 'bustling city street, high-end shopping district, blurred background',
  },
  {
    id: 'luxury-home',
    name: '豪宅内景',
    prompt:
      'modern luxury apartment living room, high-end furniture, bright window light',
  },
  {
    id: 'nature',
    name: '自然公园',
    prompt: 'scenic nature park, greenery, soft natural sunlight',
  },
  {
    id: 'beach',
    name: '阳光海滩',
    prompt: 'sunny luxury beach resort, golden sand, blue ocean, bright sunlight',
  },
]

export const POSES = [
  {
    id: 'match',
    name: '保持模特原姿势',
    prompt: 'match the pose of the reference model exactly',
  },
  {
    id: 'standing',
    name: '自信站姿',
    prompt: 'standing confidently full body shot',
  },
  {
    id: 'walking',
    name: '动态行走',
    prompt: 'walking forward with dynamic movement',
  },
  {
    id: 'sitting',
    name: '舒适坐姿',
    prompt: 'sitting relaxed in a comfortable posture',
  },
  {
    id: 'leaning',
    name: '休闲倚靠',
    prompt: 'leaning casually against a surface',
  },
]
