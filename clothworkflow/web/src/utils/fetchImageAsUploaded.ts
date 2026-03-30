import type { UploadedImage } from '../studio/types'

function randomId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`
}

/** Fetch same-origin /api/image URL and build UploadedImage for Gemini inlineData */
export async function urlToUploadedImage(
  url: string,
  id?: string
): Promise<UploadedImage> {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`获取图片失败：HTTP ${res.status}`)
  }
  const blob = await res.blob()
  const mimeType = blob.type || 'image/jpeg'
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(blob)
  })
  const base64Data = dataUrl.split(',')[1]
  if (!base64Data) {
    throw new Error('无效的图片数据')
  }
  const file = new File([blob], 'garment.jpg', { type: mimeType })
  return {
    id: id ?? randomId(),
    file,
    previewUrl: dataUrl,
    base64Data,
    mimeType,
  }
}

export function fileToUploadedImage(file: File): Promise<UploadedImage> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      const base64Data = result.split(',')[1]
      if (!base64Data) {
        reject(new Error('读取文件失败'))
        return
      }
      resolve({
        id: randomId(),
        file,
        previewUrl: result,
        base64Data,
        mimeType: file.type || 'image/jpeg',
      })
    }
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}
