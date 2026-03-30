import { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Button,
  Input,
  Typography,
  Space,
  Empty,
  message,
  Popconfirm,
  Row,
  Col,
} from 'antd'
import { UserOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import type { ModelPreset } from '../studio/types'
import {
  listModelPresets,
  addModelPreset,
  deleteModelPreset,
} from '../utils/modelPresetsStorage'
import { fileToUploadedImage } from '../utils/fetchImageAsUploaded'
import { BUILTIN_MODEL_PRESETS } from '../studio/builtinModelPresets'

const { Title, Text } = Typography

const ModelPresetsPage = () => {
  const [presets, setPresets] = useState<ModelPreset[]>([])
  const [loading, setLoading] = useState(true)
  const [name, setName] = useState('')
  const [adding, setAdding] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const list = await listModelPresets()
      setPresets(list)
    } catch {
      message.error('读取预设失败（浏览器是否禁用 IndexedDB？）')
      setPresets([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const handleAdd = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const input = (e.currentTarget.elements.namedItem('file') as HTMLInputElement)
    const file = input?.files?.[0]
    if (!file) {
      message.warning('请选择一张图片')
      return
    }
    setAdding(true)
    try {
      const img = await fileToUploadedImage(file)
      await addModelPreset({ name: name.trim() || file.name, image: img })
      input.value = ''
      setName('')
      message.success('已保存预设')
      await refresh()
    } catch (err) {
      console.error(err)
      message.error('保存失败')
    } finally {
      setAdding(false)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteModelPreset(id)
      message.success('已删除')
      await refresh()
    } catch {
      message.error('删除失败')
    }
  }

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>
      <Card
        style={{
          marginBottom: 24,
          borderRadius: 0,
          border: '2px solid #000',
          boxShadow: '4px 4px 0 #000',
        }}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Title level={3} style={{ margin: 0 }}>
            <UserOutlined style={{ marginRight: 8 }} />
            预设模特
          </Title>
          <Text type="secondary">
            内置模特随前端静态资源发布（<Text code>public/model-presets</Text>
            ）；「我的预设」保存在本机浏览器（IndexedDB）。在智能搜索的 AI
            工作室中均可从下拉框选用。
          </Text>

          <Title level={5} style={{ marginTop: 16, marginBottom: 8 }}>
            内置模特
          </Title>
          <Row gutter={[16, 16]} style={{ marginBottom: 8 }}>
            {BUILTIN_MODEL_PRESETS.map((b) => (
              <Col key={b.id} xs={12} sm={12} md={6}>
                <Card
                  size="small"
                  style={{
                    borderRadius: 0,
                    border: '1px solid #000',
                  }}
                  cover={
                    <img
                      alt={b.name}
                      src={b.publicUrl}
                      style={{
                        height: 140,
                        objectFit: 'cover',
                        objectPosition: 'top center',
                      }}
                    />
                  }
                >
                  <Card.Meta
                    title={
                      <Text style={{ fontSize: 13 }}>{b.name}</Text>
                    }
                    description={
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        四视图合成参考
                      </Text>
                    }
                  />
                </Card>
              </Col>
            ))}
          </Row>

          <Title level={5} style={{ marginTop: 8, marginBottom: 8 }}>
            我的预设
          </Title>

          <form
            onSubmit={(ev) => void handleAdd(ev)}
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 12,
              alignItems: 'flex-end',
              padding: '12px 0',
              borderTop: '1px solid #eee',
              borderBottom: '1px solid #eee',
            }}
          >
            <div>
              <Text strong style={{ display: 'block', marginBottom: 4 }}>
                显示名称
              </Text>
              <Input
                placeholder="例如：亚洲女性站姿"
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={{ width: 220 }}
                maxLength={60}
              />
            </div>
            <div>
              <Text strong style={{ display: 'block', marginBottom: 4 }}>
                图片文件
              </Text>
              <input name="file" type="file" accept="image/*" required />
            </div>
            <Button
              type="primary"
              htmlType="submit"
              icon={<PlusOutlined />}
              loading={adding}
            >
              添加预设
            </Button>
          </form>
        </Space>
      </Card>

      {loading ? (
        <Text type="secondary">加载中…</Text>
      ) : presets.length === 0 ? (
        <Empty description="暂无我的预设，可在上方表单添加" />
      ) : (
        <Row gutter={[16, 16]}>
          {presets.map((p) => {
            const thumb = `data:${p.mimeType};base64,${p.base64Data}`
            return (
              <Col key={p.id} xs={12} sm={8} md={6} lg={6}>
                <Card
                  hoverable
                  size="small"
                  style={{
                    borderRadius: 0,
                    border: '2px solid #000',
                  }}
                  cover={
                    <img
                      alt={p.name}
                      src={thumb}
                      style={{
                        height: 160,
                        objectFit: 'cover',
                        borderBottom: '1px solid #000',
                      }}
                    />
                  }
                  actions={[
                    <Popconfirm
                      key="del"
                      title="删除此预设？"
                      onConfirm={() => void handleDelete(p.id)}
                      okText="删除"
                      cancelText="取消"
                    >
                      <Button type="text" danger icon={<DeleteOutlined />} size="small">
                        删除
                      </Button>
                    </Popconfirm>,
                  ]}
                >
                  <Card.Meta
                    title={
                      <Text ellipsis style={{ maxWidth: '100%' }}>
                        {p.name}
                      </Text>
                    }
                    description={
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {new Date(p.createdAt).toLocaleString()}
                      </Text>
                    }
                  />
                </Card>
              </Col>
            )
          })}
        </Row>
      )}
    </div>
  )
}

export default ModelPresetsPage
