import type { ModelPreset, UploadedImage } from '../studio/types'

/** 将本地预设转为生图用的 UploadedImage */
export function modelPresetToUploadedImage(p: ModelPreset): UploadedImage {
  const dataUrl = `data:${p.mimeType};base64,${p.base64Data}`
  const byteChars = atob(p.base64Data)
  const bytes = new Uint8Array(byteChars.length)
  for (let i = 0; i < byteChars.length; i++) {
    bytes[i] = byteChars.charCodeAt(i)
  }
  const blob = new Blob([bytes], { type: p.mimeType })
  const safeName = p.name.replace(/[^\w\u4e00-\u9fa5\-]+/g, '_').slice(0, 40) || 'model'
  const file = new File([blob], `${safeName}.jpg`, { type: p.mimeType })
  return {
    id: p.id,
    file,
    previewUrl: dataUrl,
    base64Data: p.base64Data,
    mimeType: p.mimeType,
  }
}
