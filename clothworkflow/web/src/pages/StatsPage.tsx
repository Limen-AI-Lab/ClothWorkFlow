import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Spin, message, Typography, Space } from 'antd'
import {
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
} from '@ant-design/icons'
import { Column, Pie } from '@ant-design/charts'
import { getStats } from '../api'
import type { StatsResponse } from '../types'

const { Title, Text } = Typography

const StatsPage = () => {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<StatsResponse | null>(null)

  useEffect(() => {
    const loadStats = async () => {
      try {
        const data = await getStats()
        setStats(data)
      } catch (error) {
        message.error('Failed to load statistics')
        console.error('统计错误:', error)
      } finally {
        setLoading(false)
      }
    }
    loadStats()
  }, [])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!stats) {
    return (
      <Card>
        <Text type="secondary">No statistics data available</Text>
      </Card>
    )
  }

  // 转换数据为图表格式
  const categoryData = stats.category
    ? Object.entries(stats.category).map(([key, value]) => ({
        category: key,
        count: value as number,
      }))
    : []

  const genderData = stats.gender
    ? Object.entries(stats.gender).map(([key, value]) => ({
        type: key,
        value: value as number,
      }))
    : []

  const colorData = stats.primary_color
    ? Object.entries(stats.primary_color)
        .slice(0, 10)
        .map(([key, value]) => ({
          color: key,
          count: value as number,
        }))
    : []

  const styleData = stats.primary_style
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
        Data Statistics Overview
      </Title>

      {/* 总体统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Products"
              value={stats.total || 0}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Categories"
              value={categoryData.length}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Colors"
              value={colorData.length}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Styles"
              value={styleData.length}
              valueStyle={{ color: '#e94560' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 品类分布 */}
      {categoryData.length > 0 && (
        <Card
          title={
            <Space>
              <LineChartOutlined />
              <Text strong>Category Distribution</Text>
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
              category: { alias: 'Category' },
              count: { alias: 'Count' },
            }}
            height={300}
          />
        </Card>
      )}

      <Row gutter={[16, 16]}>
        {/* 性别分布 */}
        {genderData.length > 0 && (
          <Col xs={24} md={12}>
            <Card
              title={
                <Space>
                  <PieChartOutlined />
                  <Text strong>Gender Distribution</Text>
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

        {/* 颜色分布 */}
        {colorData.length > 0 && (
          <Col xs={24} md={12}>
            <Card
              title={
                <Space>
                  <BarChartOutlined />
                  <Text strong>Primary Color Distribution (Top 10)</Text>
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
                  color: { alias: 'Color' },
                  count: { alias: 'Count' },
                }}
                height={300}
              />
            </Card>
          </Col>
        )}

        {/* 风格分布 */}
        {styleData.length > 0 && (
          <Col xs={24} md={12}>
            <Card
              title={
                <Space>
                  <BarChartOutlined />
                  <Text strong>Style Distribution (Top 10)</Text>
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
                  style: { alias: 'Style' },
                  count: { alias: 'Count' },
                }}
                height={300}
              />
            </Card>
          </Col>
        )}
      </Row>
    </div>
  )
}

export default StatsPage
