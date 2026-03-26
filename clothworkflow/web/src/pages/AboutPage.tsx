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
        Project Introduction
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
          ClothWorkFlow - Smart Clothing Search & Recommendation System
        </Title>
        <Paragraph>
          This is an intelligent clothing search and recommendation system based on multimodal AI technology,
          combining BM25, vector retrieval, and deep learning reranking techniques to provide users with
          precise clothing search experiences.
        </Paragraph>

        <Divider />

        <Title level={4}>Core Features</Title>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div>
            <Tag color="blue" icon={<SearchOutlined />}>
              Hybrid Retrieval
            </Tag>
            <Text>Combines BM25 text retrieval, vector semantic search, and RRF fusion algorithm</Text>
          </div>
          <div>
            <Tag color="green" icon={<ApiOutlined />}>
              AI Reranking
            </Tag>
            <Text>Uses deep learning models to intelligently rerank search results</Text>
          </div>
          <div>
            <Tag color="purple" icon={<DatabaseOutlined />}>
              Multi-dimensional Analysis
            </Tag>
            <Text>50+ dimensional product attribute analysis, including color, style, material, etc.</Text>
          </div>
          <div>
            <Tag color="orange" icon={<CodeOutlined />}>
              Modern Frontend
            </Tag>
            <Text>Modern interface built with React + TypeScript + Ant Design</Text>
          </div>
        </Space>

        <Divider />

        <Title level={4}>Technical Architecture</Title>
        <Timeline
          items={[
            {
              color: 'blue',
              children: (
                <>
                  <Text strong>Frontend Stack</Text>
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
                  <Text strong>Backend Service</Text>
                  <br />
                  <Text type="secondary">
                    Python + FastAPI + Uvicorn, providing RESTful API services
                  </Text>
                </>
              ),
            },
            {
              color: 'purple',
              children: (
                <>
                  <Text strong>Search Engine</Text>
                  <br />
                  <Text type="secondary">
                    BM25 algorithm + FAISS vector database + Reranker model
                  </Text>
                </>
              ),
            },
            {
              color: 'orange',
              children: (
                <>
                  <Text strong>Data Analysis</Text>
                  <br />
                  <Text type="secondary">
                    Multi-dimensional product attribute extraction, statistical analysis, and visualization
                  </Text>
                </>
              ),
            },
          ]}
        />

        <Divider />

        <Title level={4}>API Endpoints</Title>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Card size="small" type="inner">
            <Text code>GET /api/status</Text>
            <Text type="secondary" style={{ marginLeft: 16 }}>
              Query system status
            </Text>
          </Card>
          <Card size="small" type="inner">
            <Text code>POST /api/search</Text>
            <Text type="secondary" style={{ marginLeft: 16 }}>
              Smart product search
            </Text>
          </Card>
          <Card size="small" type="inner">
            <Text code>GET /api/product/:stem</Text>
            <Text type="secondary" style={{ marginLeft: 16 }}>
              Get product details
            </Text>
          </Card>
          <Card size="small" type="inner">
            <Text code>GET /api/stats</Text>
            <Text type="secondary" style={{ marginLeft: 16 }}>
              Statistical data analysis
            </Text>
          </Card>
          <Card size="small" type="inner">
            <Text code>GET /api/config</Text>
            <Text type="secondary" style={{ marginLeft: 16 }}>
              Configuration management
            </Text>
          </Card>
        </Space>

        <Divider />

        <Paragraph type="secondary" style={{ textAlign: 'center', marginTop: 24 }}>
          ClothWorkFlow © 2026 - Smart Clothing Search & Recommendation System
        </Paragraph>
      </Card>
    </div>
  )
}

export default AboutPage
