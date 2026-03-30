import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Drawer, message } from 'antd'
import {
  PHOTO_STYLES,
  ENVIRONMENTS,
  POSES,
  type PhotoStyle,
  type UploadedImage,
  type ModelPreset,
} from '../studio/types'
import { fileToUploadedImage, urlToUploadedImage } from '../utils/fetchImageAsUploaded'
import { listModelPresets } from '../utils/modelPresetsStorage'
import { modelPresetToUploadedImage } from '../utils/modelPresetToUploaded'
import {
  BUILTIN_MODEL_PRESETS,
  builtinPickValue,
  parseBuiltinPick,
} from '../studio/builtinModelPresets'
import { generateTryOn } from '../services/geminiTryOn'

type Props = {
  open: boolean
  onClose: () => void
  /** 来自搜索勾选的商品图（已转 UploadedImage） */
  clothes: UploadedImage[]
  onClothesChange: (next: UploadedImage[]) => void
}

export function AiStudioDrawer({
  open,
  onClose,
  clothes,
  onClothesChange,
}: Props) {
  const [model, setModel] = useState<UploadedImage | null>(null)
  const [scene, setScene] = useState<UploadedImage | null>(null)
  const [selectedStyle, setSelectedStyle] = useState<PhotoStyle>(PHOTO_STYLES[0])
  const [selectedEnvironment, setSelectedEnvironment] = useState(
    ENVIRONMENTS[0].prompt
  )
  const [selectedPose, setSelectedPose] = useState(POSES[0].prompt)
  const [additionalPrompt, setAdditionalPrompt] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedImage, setGeneratedImage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [modelPresets, setModelPresets] = useState<ModelPreset[]>([])
  /** file = 使用下方本地上传；否则为预设 id */
  const [modelPick, setModelPick] = useState<'file' | string>('file')

  const resolvedApiKey = (import.meta.env.VITE_GEMINI_API_KEY || '').trim()

  useEffect(() => {
    if (!open) return
    void listModelPresets()
      .then((list) => {
        setModelPresets(list)
        setModelPick((pick) => {
          if (pick === 'file' || pick.startsWith('builtin:')) return pick
          return list.some((x) => x.id === pick) ? pick : 'file'
        })
      })
      .catch(() => setModelPresets([]))
  }, [open])

  const handleModelFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (!f) return
    try {
      setModelPick('file')
      setModel(await fileToUploadedImage(f))
    } catch {
      message.error('读取模特图失败')
    }
  }

  const onModelPresetSelect = (v: string) => {
    setModelPick(v)
    if (v === 'file') return
    const builtinId = parseBuiltinPick(v)
    if (builtinId) {
      const b = BUILTIN_MODEL_PRESETS.find((x) => x.id === builtinId)
      if (b) {
        void urlToUploadedImage(b.publicUrl, `builtin-${builtinId}`)
          .then(setModel)
          .catch(() => message.error('加载内置模特失败'))
      }
      return
    }
    const p = modelPresets.find((x) => x.id === v)
    if (p) {
      setModel(modelPresetToUploadedImage(p))
    }
  }

  const handleSceneFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (!f) return
    try {
      setScene(await fileToUploadedImage(f))
    } catch {
      message.error('读取场景图失败')
    }
  }

  const handleGenerate = async () => {
    if (!model) {
      setError('请上传一张模特参考图。')
      return
    }
    if (clothes.length === 0) {
      setError('请先在搜索结果中勾选至少一件服装。')
      return
    }
    if (!resolvedApiKey) {
      setError('未配置 API Key：请在项目根目录 .env 设置 GEMINI_API_KEY 并重启前端开发服务。')
      return
    }

    setIsGenerating(true)
    setError(null)
    setGeneratedImage(null)

    try {
      const out = await generateTryOn(resolvedApiKey, {
        clothes,
        model,
        scene,
        style: selectedStyle.promptModifier,
        aspectRatio: '3:4',
        environment: selectedEnvironment,
        pose: selectedPose,
        additionalPrompt,
      })
      setGeneratedImage(out)
      message.success('生成完成')
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : '生成图片失败，请重试。'
      setError(msg)
      message.error(msg)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <Drawer
      open={open}
      onClose={onClose}
      width="min(1240px, 98vw)"
      closable
      destroyOnClose={false}
      title={
        <span className="cw-studio-drawer-title">AI 工作室 — 试衣生图</span>
      }
      className="cw-studio-drawer"
      styles={{
        body: { padding: '12px 14px', background: '#fff' },
        header: { borderBottom: '2px solid #000' },
      }}
    >
      <div className="cw-studio-layout">
        <div className="cw-studio-panel">
          <div className="cw-studio-section-title">已选服装 · {clothes.length}/5</div>
          <p className="cw-studio-muted cw-studio-muted-tight">
            搜索页勾选；此处可移除。
          </p>
          {clothes.length === 0 ? (
            <div className="cw-studio-error-box cw-studio-error-box-compact">
              未选择服装
            </div>
          ) : (
            <div className="cw-studio-preview-list cw-studio-preview-list-row">
              {clothes.map((c) => (
                <div key={c.id} className="cw-studio-preview-chip">
                  <img
                    src={c.previewUrl}
                    alt=""
                    className="cw-studio-preview-img"
                  />
                  <button
                    type="button"
                    className="cw-studio-thumb-remove"
                    title="移除"
                    onClick={() =>
                      onClothesChange(clothes.filter((x) => x.id !== c.id))
                    }
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="cw-studio-section-title cw-studio-section-title-spaced">
            上传素材
          </div>
          <div className="cw-studio-upload-grid">
            <div className="cw-studio-upload-cell">
              <span className="cw-studio-label-inline">模特（必选）</span>
              <select
                className="cw-studio-select cw-studio-select-compact"
                value={modelPick}
                onChange={(e) => onModelPresetSelect(e.target.value)}
              >
                <option value="file">本地上传（下方选文件）</option>
                <optgroup label="内置模特（项目内）">
                  {BUILTIN_MODEL_PRESETS.map((b) => (
                    <option key={b.id} value={builtinPickValue(b.id)}>
                      {b.name}
                    </option>
                  ))}
                </optgroup>
                {modelPresets.length > 0 && (
                  <optgroup label="我的预设（本机）">
                    {modelPresets.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
              <p className="cw-studio-muted cw-studio-muted-tight">
                内置图来自{' '}
                <code style={{ fontSize: 10 }}>public/model-presets</code>；我的预设可在{' '}
                <Link to="/model-presets" onClick={onClose}>
                  预设模特
                </Link>{' '}
                管理。
              </p>
              <input
                type="file"
                accept="image/*"
                className="cw-studio-file cw-studio-file-compact"
                onChange={(e) => void handleModelFile(e)}
              />
              {model && (
                <div className="cw-studio-preview-chip cw-studio-preview-chip-solo">
                  <img
                    src={model.previewUrl}
                    alt=""
                    className="cw-studio-preview-img"
                  />
                  <button
                    type="button"
                    className="cw-studio-thumb-remove"
                    title="清除"
                    onClick={() => {
                      setModel(null)
                      setModelPick('file')
                    }}
                  >
                    ×
                  </button>
                </div>
              )}
            </div>
            <div className="cw-studio-upload-cell">
              <span className="cw-studio-label-inline">场景（可选）</span>
              <input
                type="file"
                accept="image/*"
                className="cw-studio-file cw-studio-file-compact"
                disabled={!!scene}
                onChange={(e) => void handleSceneFile(e)}
              />
              {scene && (
                <div className="cw-studio-preview-chip cw-studio-preview-chip-solo">
                  <img
                    src={scene.previewUrl}
                    alt=""
                    className="cw-studio-preview-img"
                  />
                  <button
                    type="button"
                    className="cw-studio-thumb-remove"
                    title="删除"
                    onClick={() => setScene(null)}
                  >
                    ×
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="cw-studio-section-title cw-studio-section-title-spaced">
            生成选项
          </div>
          <div className="cw-studio-config-grid">
            <div className="cw-studio-field">
              <label className="cw-studio-label cw-studio-label-compact">
                摄影风格
              </label>
              <select
                className="cw-studio-select cw-studio-select-compact"
                value={selectedStyle.id}
                onChange={(e) => {
                  const s = PHOTO_STYLES.find((x) => x.id === e.target.value)
                  if (s) setSelectedStyle(s)
                }}
              >
                {PHOTO_STYLES.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="cw-studio-field">
              <label className="cw-studio-label cw-studio-label-compact">
                环境
                {scene && (
                  <span className="cw-studio-label-note">（已用场景图）</span>
                )}
              </label>
              <select
                className="cw-studio-select cw-studio-select-compact"
                disabled={!!scene}
                value={selectedEnvironment}
                onChange={(e) => setSelectedEnvironment(e.target.value)}
              >
                {ENVIRONMENTS.map((env) => (
                  <option key={env.id} value={env.prompt}>
                    {env.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="cw-studio-field cw-studio-field-full">
              <label className="cw-studio-label cw-studio-label-compact">
                姿势
              </label>
              <select
                className="cw-studio-select cw-studio-select-compact"
                value={selectedPose}
                onChange={(e) => setSelectedPose(e.target.value)}
              >
                {POSES.map((p) => (
                  <option key={p.id} value={p.prompt}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="cw-studio-field cw-studio-field-full">
              <label className="cw-studio-label cw-studio-label-compact">
                额外指令
              </label>
              <textarea
                className="cw-studio-textarea cw-studio-textarea-compact"
                rows={2}
                placeholder="可选，如：看镜头…"
                value={additionalPrompt}
                onChange={(e) => setAdditionalPrompt(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="cw-studio-error-box cw-studio-error-box-compact">
              {error}
            </div>
          )}

          <button
            type="button"
            className="cw-studio-btn cw-studio-btn-block cw-studio-btn-block-compact"
            disabled={
              isGenerating ||
              !model ||
              clothes.length === 0 ||
              !resolvedApiKey
            }
            onClick={() => void handleGenerate()}
          >
            {isGenerating ? '生成中…' : '开始生成'}
          </button>
        </div>

        <div className="cw-studio-panel cw-studio-panel-out">
          <div className="cw-studio-section-title">生成结果</div>
          <div className="cw-studio-result-frame">
            {generatedImage ? (
              <img
                src={generatedImage}
                alt="生成结果"
                className="cw-studio-result-img"
              />
            ) : (
              <div className="cw-studio-result-placeholder">
                {isGenerating ? <p>正在处理…</p> : <p>等待生成</p>}
              </div>
            )}
          </div>
          {generatedImage && (
            <div className="cw-studio-download-row">
              <a href={generatedImage} download="clothworkflow-tryon.png">
                <button
                  type="button"
                  className="cw-studio-btn cw-studio-btn-sm"
                >
                  下载原图
                </button>
              </a>
            </div>
          )}
        </div>
      </div>
    </Drawer>
  )
}
