/**
 * 与 ai-studio/services/geminiService.ts 的 generateTryOn 保持一致：
 * - GoogleGenAI + models.generateContent（model / contents.parts / config.imageConfig）
 * - 默认模型 gemini-3-pro-image-preview（可通过 VITE_GEMINI_IMAGE_MODEL 覆盖）
 * - API Key：运行时传入；构建时可注入 VITE_GEMINI_API_KEY（对应参考项目里的 process.env.API_KEY）
 */
import { GoogleGenAI } from '@google/genai'
import type { GenerationConfig } from '../studio/types'

/** 与 ai-studio 一致；可用 VITE_GEMINI_IMAGE_MODEL 覆盖 */
const IMAGE_MODEL =
  import.meta.env.VITE_GEMINI_IMAGE_MODEL || 'gemini-3-pro-image-preview'

export async function generateTryOn(
  apiKey: string,
  config: GenerationConfig
): Promise<string> {
  if (!apiKey.trim()) {
    throw new Error('请填写 Gemini API Key（或配置 VITE_GEMINI_API_KEY）')
  }

  const {
    clothes,
    model,
    scene,
    style,
    aspectRatio,
    pose,
    environment,
    additionalPrompt,
  } = config

  if (!model) {
    throw new Error('需要上传模特图片')
  }

  // 与参考文件相同的提示词结构（中英文标签 + 条件环境/姿势）
  const promptText = `生成一张逼真的时尚照片。
  
  指令:
  1. 使用“模特参考图”中的人物作为时尚模特。保持其身体特征。
  2. 给模特穿上提供的“服装单品”。自然地替换掉模特原本的衣服。根据模特的姿势和体型，逼真地贴合衣物。
  3. 环境: ${scene ? '将模特放置在“场景参考图”所示的环境中。' : `将模特放置在以下场景中: ${environment || '中性摄影棚背景'}.`}
  4. 姿势: ${pose || '保持模特参考图中的姿势。'}
  5. 应用以下摄影风格: ${style}.
  6. 确保模特、服装和场景之间的光照、阴影和色温一致。
  7. 输出必须是一张高质量、逼真的照片。
  ${additionalPrompt ? `8. 额外要求: ${additionalPrompt}` : ''}`

  const parts: Array<
    | { text: string }
    | { inlineData: { mimeType: string; data: string } }
  > = []

  parts.push({
    text: '模特参考图 (Model Reference Image):',
  })
  parts.push({
    inlineData: {
      mimeType: model.mimeType,
      data: model.base64Data,
    },
  })

  clothes.forEach((cloth, index) => {
    parts.push({
      text: `服装单品 ${index + 1} (Clothing Item):`,
    })
    parts.push({
      inlineData: {
        mimeType: cloth.mimeType,
        data: cloth.base64Data,
      },
    })
  })

  if (scene) {
    parts.push({
      text: '场景参考图 (Scene Reference Image):',
    })
    parts.push({
      inlineData: {
        mimeType: scene.mimeType,
        data: scene.base64Data,
      },
    })
  }

  parts.push({
    text: promptText,
  })

  // 每次请求新建实例，确保使用当前填写的 API Key（与参考实现一致）
  const ai = new GoogleGenAI({ apiKey: apiKey.trim() })

  try {
    const response = await ai.models.generateContent({
      model: IMAGE_MODEL,
      contents: {
        parts,
      },
      config: {
        imageConfig: {
          aspectRatio,
          imageSize: '1K',
        },
      },
    })

    for (const part of response.candidates?.[0]?.content?.parts || []) {
      if (part.inlineData) {
        return `data:image/png;base64,${part.inlineData.data}`
      }
    }

    throw new Error('未生成图片。')
  } catch (error) {
    console.error('Gemini API Error:', error)
    throw error
  }
}
