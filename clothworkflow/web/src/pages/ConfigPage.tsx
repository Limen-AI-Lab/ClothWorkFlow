import { useState, useEffect } from 'react'
import { Card, Button, message, Typography, Space, Spin } from 'antd'
import { SettingOutlined, SaveOutlined, ReloadOutlined } from '@ant-design/icons'
import { Input } from 'antd'
import { getConfig, updateConfig } from '../api'

const { Title, Text } = Typography
const { TextArea } = Input

const ConfigPage = () => {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [yamlContent, setYamlContent] = useState('')
  const [originalYaml, setOriginalYaml] = useState('')

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setLoading(true)
    try {
      const data = await getConfig()
      setYamlContent(data.yaml)
      setOriginalYaml(data.yaml)
    } catch (error) {
      message.error('Failed to load configuration')
      console.error('配置错误:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateConfig({ yaml: yamlContent })
      setOriginalYaml(yamlContent)
      message.success('Configuration saved')
    } catch (error) {
      message.error('Failed to save configuration')
      console.error('保存错误:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    setYamlContent(originalYaml)
    message.info('Reset to last saved configuration')
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Title level={2} style={{ marginBottom: 24 }}>
        <SettingOutlined style={{ marginRight: 8 }} />
        Settings
      </Title>

      <Card
        title={<Text strong>YAML 配置文件</Text>}
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleReset}
              disabled={yamlContent === originalYaml}
            >
              Reset
            </Button>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSave}
              loading={saving}
              disabled={yamlContent === originalYaml}
            >
              Save Configuration
            </Button>
          </Space>
        }
        style={{
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}
      >
        <TextArea
          value={yamlContent}
          onChange={(e) => setYamlContent(e.target.value)}
          rows={25}
          style={{
            fontFamily: 'Consolas, Monaco, "Courier New", monospace',
            fontSize: 14,
          }}
        />
        <div style={{ marginTop: 16 }}>
          <Text type="secondary">
            Click "Save Configuration" button to apply changes. Note: Configuration errors may cause system issues.
          </Text>
        </div>
      </Card>
    </div>
  )
}

export default ConfigPage
