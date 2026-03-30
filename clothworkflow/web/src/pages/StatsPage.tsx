import { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Spin,
  message,
  Typography,
  Space,
  Alert,
  Button,
  Select,
} from 'antd'
import {
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
} from '@ant-design/icons'
import { Column, Pie } from '@ant-design/charts'
import { getStats, getStatus, getAnalysisDirs, loadData } from '../api'
import type { StatsResponse, AnalysisDir } from '../types'

const { Title, Text } = Typography

const StatsPage = () => {
  const [dataLoaded, setDataLoaded] = useState(false)
  const [productCount, setProductCount] = useState(0)
  const [analysisDirs, setAnalysisDirs] = useState<AnalysisDir[]>([])
  const [selectedDir, setSelectedDir] = useState<string | undefined>(undefined)
  const [loadBusy, setLoadBusy] = useState(false)

  const [statsLoading, setStatsLoading] = useState(true)
  const [stats, setStats] = useState<StatsResponse | null>(null)

  const refreshBackendState = useCallback(async () => {
    try {
      const [st, dirs] = await Promise.all([getStatus(), getAnalysisDirs()])
      setDataLoaded(st.loaded)
      setProductCount(st.count)
      setAnalysisDirs(dirs.dirs)
      setSelectedDir((prev) => prev ?? dirs.dirs[0]?.path)
    } catch {
      setDataLoaded(false)
    }
  }, [])

  const loadStats = useCallback(async () => {
    setStatsLoading(true)
    try {
      const data = await getStats()
      setStats(data)
    } catch (error) {
      message.error('加载统计数据失败')
      console.error('统计错误:', error)
      setStats(null)
    } finally {
      setStatsLoading(false)
    }
  }, [])

  useEffect(() => {
    void refreshBackendState()
    const t = setInterval(() => void refreshBackendState(), 8000)
    return () => clearInterval(t)
  }, [refreshBackendState])

  useEffect(() => {
    void loadStats()
  }, [loadStats])

  const handleLoadDataset = async () => {
    if (!selectedDir) {
      message.warning('请选择分析数据目录')
      return
    }
    setLoadBusy(true)
    try {
      const res = await loadData({ analysis_dir: selectedDir })
      setDataLoaded(true)
      setProductCount(res.count)
      message.success(`已加载 ${res.count} 件商品`)
      await refreshBackendState()
      await loadStats()
    } catch (e: unknown) {
      const detail =
        e && typeof e === 'object' && 'response' in e
          ? (e as { response?: { data?: { detail?: string } } }).response?.data
              ?.detail
          : undefined
      message.error(
        typeof detail === 'string'
          ? detail
          : '加载数据失败（请查看后端日志或模型配置）'
      )
    } finally {
      setLoadBusy(false)
    }
  }

  const categoryData = stats?.category
    ? Object.entries(stats.category).map(([key, value]) => ({
        category: key,
        count: value as number,
      }))
    : []

  const genderData = stats?.gender
    ? Object.entries(stats.gender).map(([key, value]) => ({
        type: key,
        value: value as number,
      }))
    : []

  const colorData = stats?.primary_color
    ? Object.entries(stats.primary_color)
        .slice(0, 10)
        .map(([key, value]) => ({
          color: key,
          count: value as number,
        }))
    : []

  const styleData = stats?.primary_style
    ? Object.entries(stats.primary_style)
        .slice(0, 10)
        .map(([key, value]) => ({
          style: key,
          count: value as number,
        }))
    : []

  return (
    <div style={{ maxWidth: 1600, margin: '0 auto' }}>
      <Title level={2} style={{ marginBottom: 24 }}>
        <BarChartOutlined style={{ marginRight: 8 }} />
        数据统计概览
      </Title>

      <Card
        title="数据加载"
        style={{
          marginBottom: 24,
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {!dataLoaded && (
            <Alert
              type="warning"
              showIcon
              message="尚未加载搜索索引"
              description="未加载分析数据集前搜索会返回 HTTP 400。请选择目录并点击「加载数据集」；首次加载可能需下载模型，耗时数分钟。"
              style={{ width: '100%' }}
            />
          )}
          {analysisDirs.length > 0 ? (
            <Space wrap style={{ width: '100%' }} align="center">
              <Select
                style={{ minWidth: 280, maxWidth: '100%' }}
                placeholder="分析数据目录"
                value={selectedDir}
                options={analysisDirs.map((d) => ({
                  value: d.path,
                  label: `${d.label} (${d.type})`,
                }))}
                onChange={setSelectedDir}
              />
              <Button
                type="primary"
                loading={loadBusy}
                onClick={() => void handleLoadDataset()}
              >
                加载数据集
              </Button>
              {dataLoaded && (
                <Text type="success">
                  就绪 — 内存中 {productCount} 件商品
                </Text>
              )}
            </Space>
          ) : (
            <Text type="secondary">未检测到可用分析目录，请检查后端配置。</Text>
          )}
        </Space>
      </Card>

      {statsLoading ? (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <Spin size="large" />
        </div>
      ) : !stats ? (
        <Card>
          <Text type="secondary">暂无统计数据</Text>
        </Card>
      ) : (
        <>
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="商品总数"
                  value={stats.total || 0}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="品类数"
                  value={categoryData.length}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="颜色种类"
                  value={colorData.length}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="风格种类"
                  value={styleData.length}
                  valueStyle={{ color: '#e94560' }}
                />
              </Card>
            </Col>
          </Row>

          {categoryData.length > 0 && (
            <Card
              title={
                <Space>
                  <LineChartOutlined />
                  <Text strong>品类分布</Text>
                </Space>
              }
              style={{ marginBottom: 24 }}
            >
              <Column
                data={categoryData}
                xField="category"
                yField="count"
                label={{
                  position: 'top',
                  style: { fill: '#000', opacity: 0.6 },
                }}
                xAxis={{
                  label: {
                    autoRotate: true,
                    autoHide: false,
                  },
                }}
                meta={{
                  category: { alias: '品类' },
                  count: { alias: '数量' },
                }}
                height={300}
              />
            </Card>
          )}

          <Row gutter={[16, 16]}>
            {genderData.length > 0 && (
              <Col xs={24} md={12}>
                <Card
                  title={
                    <Space>
                      <PieChartOutlined />
                      <Text strong>性别分布</Text>
                    </Space>
                  }
                >
                  <Pie
                    data={genderData}
                    angleField="value"
                    colorField="type"
                    radius={0.8}
                    label={{
                      type: 'outer',
                      content: '{name} {percentage}',
                    }}
                    interactions={[
                      { type: 'element-active' },
                      { type: 'pie-legend-active' },
                    ]}
                    height={300}
                  />
                </Card>
              </Col>
            )}

            {colorData.length > 0 && (
              <Col xs={24} md={12}>
                <Card
                  title={
                    <Space>
                      <BarChartOutlined />
                      <Text strong>主色分布（前 10）</Text>
                    </Space>
                  }
                >
                  <Column
                    data={colorData}
                    xField="color"
                    yField="count"
                    label={{
                      position: 'top',
                      style: { fill: '#000', opacity: 0.6 },
                    }}
                    xAxis={{
                      label: {
                        autoRotate: true,
                      },
                    }}
                    meta={{
                      color: { alias: '颜色' },
                      count: { alias: '数量' },
                    }}
                    height={300}
                  />
                </Card>
              </Col>
            )}

            {styleData.length > 0 && (
              <Col xs={24} md={12}>
                <Card
                  title={
                    <Space>
                      <BarChartOutlined />
                      <Text strong>风格分布（前 10）</Text>
                    </Space>
                  }
                >
                  <Column
                    data={styleData}
                    xField="style"
                    yField="count"
                    label={{
                      position: 'top',
                      style: { fill: '#000', opacity: 0.6 },
                    }}
                    xAxis={{
                      label: {
                        autoRotate: true,
                      },
                    }}
                    meta={{
                      style: { alias: '风格' },
                      count: { alias: '数量' },
                    }}
                    height={300}
                  />
                </Card>
              </Col>
            )}
          </Row>
        </>
      )}
    </div>
  )
}

export default StatsPage
