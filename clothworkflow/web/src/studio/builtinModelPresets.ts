/**
 * 随前端静态资源提供的内置模特图（public/model-presets/）。
 * 每张图为同一人四视图合成白底参考，供试衣生图选用。
 */
export interface BuiltinModelPreset {
  id: string
  /** 界面展示名 */
  name: string
  /** 相对站点根路径 */
  publicUrl: string
}

export const BUILTIN_MODEL_PRESETS: BuiltinModelPreset[] = [
  {
    id: 'male-blond',
    name: '金发男模 · 白T四视图',
    publicUrl: '/model-presets/白T金发男模-四视图.png',
  },
  {
    id: 'female-deep-skin',
    name: '深肤色女模 · 白T四视图',
    publicUrl: '/model-presets/白T深肤色女模-四视图.png',
  },
  {
    id: 'female-east-asian',
    name: '亚裔女模 · 白T四视图',
    publicUrl: '/model-presets/白T亚裔女模-四视图.png',
  },
  {
    id: 'male-dark-hair',
    name: '深发男模 · 白T四视图',
    publicUrl: '/model-presets/白T深发男模-四视图.png',
  },
]

export function builtinPickValue(id: string): string {
  return `builtin:${id}`
}

export function parseBuiltinPick(v: string): string | null {
  if (!v.startsWith('builtin:')) return null
  return v.slice('builtin:'.length)
}
