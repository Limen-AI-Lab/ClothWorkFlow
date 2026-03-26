import { useState, useEffect } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { Layout, Menu, Badge, Spin, Typography } from 'antd'
import {
  SearchOutlined,
  BarChartOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons'
import SearchPage from './pages/SearchPage'
import StatsPage from './pages/StatsPage'
import ConfigPage from './pages/ConfigPage'
import AboutPage from './pages/AboutPage'
import { getStatus } from './api'
import type { StatusResponse } from './types'

const { Header, Sider, Content } = Layout
const { Text } = Typography

function App() {
  const [collapsed, setCollapsed] = useState(false)
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const location = useLocation()

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const data = await getStatus()
        setStatus(data)
      } catch (error) {
        console.error('加载状态失败:', error)
      } finally {
        setLoading(false)
      }
    }
    loadStatus()
    const interval = setInterval(loadStatus, 5000) // 每5秒刷新状态
    return () => clearInterval(interval)
  }, [])

  const menuItems = [
    {
      key: '/search',
      icon: <SearchOutlined />,
      label: <Link to="/search">Smart Search</Link>,
    },
    {
      key: '/stats',
      icon: <BarChartOutlined />,
      label: <Link to="/stats">Data Overview</Link>,
    },
    {
      key: '/config',
      icon: <SettingOutlined />,
      label: <Link to="/config">Settings</Link>,
    },
    {
      key: '/about',
      icon: <InfoCircleOutlined />,
      label: <Link to="/about">About</Link>,
    },
  ]

  const selectedKey = location.pathname || '/search'

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{
          background: '#1a1a2e',
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: collapsed ? 16 : 20,
            fontWeight: 'bold',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          {collapsed ? 'CW' : 'ClothWorkFlow'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          style={{ background: '#1a1a2e', borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <Text strong style={{ fontSize: 18 }}>
            Smart Clothing Search & Recommendation System
          </Text>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {loading ? (
              <Spin indicator={<LoadingOutlined spin />} size="small" />
            ) : status?.loaded ? (
              <Badge status="success" text={`Loaded ${status.count} products`} />
            ) : (
              <Badge status="warning" text="No data loaded" />
            )}
          </div>
        </Header>
        <Content
          style={{
            margin: '24px',
            padding: 24,
            minHeight: 280,
            background: '#f5f5f5',
            borderRadius: 8,
          }}
        >
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/stats" element={<StatsPage />} />
            <Route path="/config" element={<ConfigPage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default App
