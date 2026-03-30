import { Card, Typography, Timeline, Tag, Space, Divider } from 'antd'
import {
  InfoCircleOutlined,
  RocketOutlined,
  CodeOutlined,
  ApiOutlined,
  DatabaseOutlined,
  SearchOutlined,
} from '@ant-design/icons'

const { Title, Paragraph, Text } = Typography

const AboutPage = () => {
  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Title level={2} style={{ marginBottom: 24 }}>
        <InfoCircleOutlined style={{ marginRight: 8 }} />
        项目介绍
      </Title>

      <Card
        style={{
          marginBottom: 24,
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}
      >
        <Title level={3}>
          <RocketOutlined style={{ marginRight: 8 }} />
          ClothWorkFlow — 智能服饰搜索与推荐
        </Title>
        <Paragraph>
          基于多模态 AI 的智能服饰搜索与推荐系统，融合 BM25、向量检索与深度学习重排序，
          为用户提供更精准的服饰检索体验。
        </Paragraph>

        <Divider />

        <Title level={4}>核心能力</Title>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div>
            <Tag color="blue" icon={<SearchOutlined />}>
              混合检索
            </Tag>
            <Text>BM25 文本检索、向量语义搜索与 RRF 融合</Text>
          </div>
          <div>
            <Tag color="green" icon={<ApiOutlined />}>
              AI 重排序
            </Tag>
            <Text>深度学习模型对搜索结果智能重排</Text>
          </div>
          <div>
            <Tag color="purple" icon={<DatabaseOutlined />}>
              多维分析
            </Tag>
            <Text>50+ 维商品属性分析，涵盖色彩、风格、面料等</Text>
          </div>
          <div>
            <Tag color="orange" icon={<CodeOutlined />}>
              现代前端
            </Tag>
            <Text>React + TypeScript + Ant Design 构建的界面</Text>
          </div>
        </Space>

        <Divider />

        <Title level={4}>技术架构</Title>
        <Timeline
          items={[
            {
              color: 'blue',
              children: (
                <>
                  <Text strong>前端</Text>
                  <br />
                  <Text type="secondary">
                    React 19 + TypeScript + Ant Design + Vite + React Router
                  </Text>
                </>
              ),
            },
            {
              color: 'green',
              children: (
                <>
                  <Text strong>后端服务</Text>
                  <br />
                  <Text type="secondary">
                    Python + FastAPI + Uvicorn，提供 RESTful API
                  </Text>
                </>
              ),
            },
            {
              color: 'purple',
              children: (
                <>
                  <Text strong>搜索引擎</Text>
                  <br />
                  <Text type="secondary">
                    BM25 + FAISS 向量库 + Reranker 模型
                  </Text>
                </>
              ),
            },
            {
              color: 'orange',
              children: (
                <>
                  <Text strong>数据分析</Text>
                  <br />
                  <Text type="secondary">
                    多维商品属性抽取、统计分析与可视化
                  </Text>
                </>
              ),
            },
          ]}
        />

        <Divider />

        <Title level={4}>API 端点</Title>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Card size="small" type="inner">
            <Text code>GET /api/status</Text>
            <Text type="secondary" style={{ marginLeft: 16 }}>
              查询系统状态
            </Text>
          </Card>
          <Card size="small" type="inner">
            <Text code>POST /api/search</Text>
            <Text type="secondary" style={{ marginLeft: 16 }}>
              智能商品搜索
            </Text>
          </Card>
          <Card size="small" type="inner">
            <Text code>GET /api/product/:stem</Text>
            <Text type="secondary" style={{ marginLeft: 16 }}>
              获取商品详情
            </Text>
          </Card>
          <Card size="small" type="inner">
            <Text code>GET /api/stats</Text>
            <Text type="secondary" style={{ marginLeft: 16 }}>
              统计数据
            </Text>
          </Card>
          <Card size="small" type="inner">
            <Text code>GET /api/config</Text>
            <Text type="secondary" style={{ marginLeft: 16 }}>
              配置管理
            </Text>
          </Card>
        </Space>

        <Divider />

        <Paragraph type="secondary" style={{ textAlign: 'center', marginTop: 24 }}>
          ClothWorkFlow © 2026 — 智能服饰搜索与推荐系统
        </Paragraph>
      </Card>
    </div>
  )
}

export default AboutPage
