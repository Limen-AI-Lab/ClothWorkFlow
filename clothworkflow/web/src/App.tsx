import { useState, useEffect } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { Layout, Menu, Badge, Spin, Typography, ConfigProvider } from 'antd'
import {
  SearchOutlined,
  BarChartOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  UserOutlined,
} from '@ant-design/icons'
import SearchPage from './pages/SearchPage'
import StatsPage from './pages/StatsPage'
import ModelPresetsPage from './pages/ModelPresetsPage'
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
      label: <Link to="/search">智能搜索</Link>,
    },
    {
      key: '/stats',
      icon: <BarChartOutlined />,
      label: <Link to="/stats">数据概览</Link>,
    },
    {
      key: '/model-presets',
      icon: <UserOutlined />,
      label: <Link to="/model-presets">预设模特</Link>,
    },
    {
      key: '/config',
      icon: <SettingOutlined />,
      label: <Link to="/config">设置</Link>,
    },
    {
      key: '/about',
      icon: <InfoCircleOutlined />,
      label: <Link to="/about">关于</Link>,
    },
  ]

  const selectedKey = location.pathname || '/search'

  return (
    <ConfigProvider
      theme={{
        token: {
          borderRadius: 0,
          colorPrimary: '#000000',
          colorBorder: '#000000',
          fontFamily:
            "'Courier New', Courier, 'Microsoft YaHei', monospace, sans-serif",
        },
        components: {
          Card: { borderRadiusLG: 0, paddingLG: 20 },
          Button: {
            borderRadius: 0,
            fontWeight: 700,
            controlHeight: 40,
          },
          Menu: { itemBorderRadius: 0 },
          Layout: { headerBg: '#ffffff', bodyBg: '#fafafa' },
        },
      }}
    >
      <Layout className="cw-app-aistudio" style={{ minHeight: '100vh' }}>
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          className="cw-aistudio-sider"
          width={240}
        >
          <div className="cw-aistudio-logo">
            {collapsed ? 'CW' : '服饰工作流'}
          </div>
          <Menu
            theme="light"
            mode="inline"
            selectedKeys={[selectedKey]}
            items={menuItems}
            className="cw-aistudio-menu"
          />
        </Sider>
        <Layout>
          <Header className="cw-aistudio-header">
            <Text strong className="cw-aistudio-header-title">
              智能服饰搜索 / AI 工作室
            </Text>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              {loading ? (
                <Spin indicator={<LoadingOutlined spin />} size="small" />
              ) : status?.loaded ? (
                <Badge
                  status="success"
                  text={`已加载 ${status.count} 件`}
                  className="cw-aistudio-badge"
                />
              ) : (
                <Badge
                  status="warning"
                  text="未加载索引"
                  className="cw-aistudio-badge"
                />
              )}
            </div>
          </Header>
          <Content className="cw-aistudio-content">
            <Routes>
              <Route path="/" element={<SearchPage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/stats" element={<StatsPage />} />
              <Route path="/model-presets" element={<ModelPresetsPage />} />
              <Route path="/config" element={<ConfigPage />} />
              <Route path="/about" element={<AboutPage />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  )
}

export default App
