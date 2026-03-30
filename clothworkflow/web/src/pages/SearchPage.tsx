import { useState, useEffect } from 'react'
import {
  Input,
  Row,
  Col,
  Card,
  Tag,
  Progress,
  Badge,
  Skeleton,
  Drawer,
  Descriptions,
  Timeline,
  Image,
  Space,
  Typography,
  message,
  Empty,
  Statistic,
  Alert,
  Button,
  Checkbox,
  InputNumber,
} from 'antd'
import {
  SearchOutlined,
  ClockCircleOutlined,
  FireOutlined,
  StarOutlined,
  ExperimentOutlined,
} from '@ant-design/icons'
import {
  searchProducts,
  getProduct,
  getImageUrl,
  getStatus,
} from '../api'
import type {
  SearchResponse,
  SearchResult,
  ProductResponse,
} from '../types'
import type { UploadedImage } from '../studio/types'
import { urlToUploadedImage } from '../utils/fetchImageAsUploaded'
import { AiStudioDrawer } from '../components/AiStudioDrawer'

const { Search } = Input
const { Text, Title } = Typography

const MAX_STUDIO_PIECES = 5

function studioKey(r: SearchResult): string {
  const prefix = r.slot ? `${r.slot}-` : ''
  return r.image_url || `${prefix}rank-${r.rank}-${r.title}`
}

// Color mapping
const colorMap: Record<string, string> = {
  红色: '#ff4d4f',
  橙色: '#ff7a45',
  黄色: '#ffd666',
  绿色: '#52c41a',
  青色: '#13c2c2',
  蓝色: '#1890ff',
  紫色: '#722ed1',
  粉色: '#eb2f96',
  棕色: '#8c6239',
  黑色: '#262626',
  白色: '#ffffff',
  灰色: '#8c8c8c',
  米色: '#d9d9d9',
}

const SearchPage = () => {
  const [query, setQuery] = useState('')
  const [topN, setTopN] = useState(20)
  const [loading, setLoading] = useState(false)
  const [dataLoaded, setDataLoaded] = useState(false)
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<ProductResponse | null>(
    null
  )
  const [productLoading, setProductLoading] = useState(false)
  const [selectedStudioKeys, setSelectedStudioKeys] = useState<string[]>([])
  const [studioOpen, setStudioOpen] = useState(false)
  const [studioClothes, setStudioClothes] = useState<UploadedImage[]>([])
  const [studioPrefillBusy, setStudioPrefillBusy] = useState(false)
  const [useLlmRoute, setUseLlmRoute] = useState(false)
  /** null = 后端按 top_n 与 slot 数自动分配 */
  const [perSlotTopN, setPerSlotTopN] = useState<number | null>(null)
  const [geminiConfigured, setGeminiConfigured] = useState<boolean | null>(null)

  const toggleStudioSelection = (r: SearchResult) => {
    const k = studioKey(r)
    setSelectedStudioKeys((prev) => {
      if (prev.includes(k)) {
        return prev.filter((x) => x !== k)
      }
      if (prev.length >= MAX_STUDIO_PIECES) {
        message.warning(`最多选择 ${MAX_STUDIO_PIECES} 件服装用于生图`)
        return prev
      }
      return [...prev, k]
    })
  }

  const openStudioDrawer = async () => {
    if (selectedStudioKeys.length === 0) {
      message.warning('请先在结果中勾选服装')
      return
    }
    if (!searchResult) return
    setStudioPrefillBusy(true)
    try {
      const picked = searchResult.results.filter((r) =>
        selectedStudioKeys.includes(studioKey(r))
      )
      const imgs = await Promise.all(
        picked.map((r) => {
          const u = r.image_url
          if (!u) {
            throw new Error('缺少图片地址')
          }
          return urlToUploadedImage(getImageUrl(u), studioKey(r))
        })
      )
      setStudioClothes(imgs)
      setStudioOpen(true)
    } catch {
      message.error('加载勾选商品图失败，请确认图片可访问')
    } finally {
      setStudioPrefillBusy(false)
    }
  }

  const refreshIndexStatus = async () => {
    try {
      const st = await getStatus()
      setDataLoaded(st.loaded)
      setGeminiConfigured(st.gemini_configured ?? null)
    } catch {
      setDataLoaded(false)
      setGeminiConfigured(null)
    }
  }

  useEffect(() => {
    void refreshIndexStatus()
    const t = setInterval(() => void refreshIndexStatus(), 8000)
    return () => clearInterval(t)
  }, [])

  // Execute search
  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      message.warning('请输入搜索关键词')
      return
    }
    if (!dataLoaded) {
      message.warning('请先在「数据概览」页面加载数据集（或启用服务端自动加载）')
      return
    }

    setLoading(true)
    try {
      const result = await searchProducts({
        query: searchQuery,
        top_n: topN,
        llm_route: useLlmRoute,
        ...(useLlmRoute && perSlotTopN != null
          ? { per_slot_top_n: perSlotTopN }
          : {}),
      })
      setSearchResult(result)
      setSelectedStudioKeys([])
      const modeHint =
        result.llm_route?.mode === 'outfit'
          ? '（搭配：分品类检索）'
          : result.llm_route?.mode === 'single'
            ? '（单品）'
            : ''
      message.success(`找到 ${result.results.length} 件相关商品${modeHint}`)
    } catch (e: unknown) {
      const detail =
        e && typeof e === 'object' && 'response' in e
          ? (e as { response?: { data?: { detail?: string } } }).response?.data
              ?.detail
          : undefined
      message.error(
        typeof detail === 'string'
          ? detail
          : '搜索失败，请检查后端服务或网络'
      )
      console.error('Search error:', e)
    } finally {
      setLoading(false)
    }
  }

  // Load product details
  const handleShowDetail = async (result: SearchResult) => {
    setDrawerVisible(true)
    setProductLoading(true)
    try {
      // Extract stem from image_url (/api/image?path=/.../product_001.jpg)
      const urlPath = decodeURIComponent(result.image_url?.split('path=')[1] || '')
      const stem = urlPath.split('/').pop()?.replace(/\.[^.]+$/, '') || ''
      const product = await getProduct(stem)
      setSelectedProduct(product)
    } catch (error) {
      message.error('加载商品详情失败')
      console.error('Details error:', error)
    } finally {
      setProductLoading(false)
    }
  }

  // Get score color
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return '#52c41a'
    if (score >= 0.6) return '#1890ff'
    if (score >= 0.4) return '#faad14'
    return '#ff4d4f'
  }

  // Render score progress bar
  const renderScoreProgress = (label: string, score: number) => (
    <div style={{ marginBottom: 12 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: 4,
        }}
      >
        <Text type="secondary" style={{ fontSize: 12 }}>
          {label}
        </Text>
        <Text strong style={{ fontSize: 12 }}>
          {(score * 100).toFixed(1)}%
        </Text>
      </div>
      <Progress
        percent={score * 100}
        strokeColor={getScoreColor(score)}
        showInfo={false}
        size="small"
      />
    </div>
  )

  return (
    <div style={{ maxWidth: 1600, margin: '0 auto' }}>
      {!dataLoaded && (
        <Alert
          type="warning"
          showIcon
          message="尚未加载搜索索引"
          description="请打开左侧「数据概览」，在「数据加载」中选择分析目录并点击「加载数据集」。首次加载可能需下载模型，耗时数分钟。"
          style={{ width: '100%', marginBottom: 24 }}
        />
      )}

      <Card
        style={{
          marginBottom: 24,
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}
      >
        <Title level={3} style={{ margin: 0, marginBottom: 16 }}>
          <SearchOutlined style={{ marginRight: 8 }} />
          智能搜索
        </Title>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Search
            placeholder="输入商品描述，例如：休闲风蓝色 T 恤"
            size="large"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onSearch={handleSearch}
            enterButton="搜索"
            loading={loading}
            style={{ width: '100%', fontSize: 16 }}
          />
          <Space align="center" wrap>
            <Text type="secondary">返回条数</Text>
            <InputNumber
              min={5}
              max={50}
              value={topN}
              onChange={(v) => {
                if (typeof v === 'number' && !Number.isNaN(v)) {
                  setTopN(Math.min(50, Math.max(5, v)))
                }
              }}
              size="large"
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              （5–50）
            </Text>
            <Checkbox
              checked={useLlmRoute}
              onChange={(e) => setUseLlmRoute(e.target.checked)}
            >
              智能理解搭配（Gemini 3 Flash）
            </Checkbox>
            {useLlmRoute && (
              <>
                <Text type="secondary">每品类条数</Text>
                <InputNumber
                  min={3}
                  max={20}
                  placeholder="自动"
                  value={perSlotTopN ?? undefined}
                  onChange={(v) => {
                    if (v == null || (typeof v === 'number' && Number.isNaN(v))) {
                      setPerSlotTopN(null)
                    } else if (typeof v === 'number') {
                      setPerSlotTopN(Math.min(20, Math.max(3, v)))
                    }
                  }}
                  size="large"
                />
              </>
            )}
          </Space>
          {useLlmRoute && (
            <Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
              开启后由后端调用 Gemini 判断单品或搭配；搭配时在上装/下装/连衣裙等分桶内分别检索。需在运行 API
              的环境中设置 GEMINI_API_KEY。
              {geminiConfigured === false && (
                <span style={{ color: '#fa8c16', marginLeft: 8 }}>
                  当前后端未检测到 GEMINI_API_KEY。
                </span>
              )}
            </Text>
          )}
        </Space>
      </Card>

      {/* Search Statistics */}
      {searchResult && (
        <Card
          style={{
            marginBottom: 24,
            borderRadius: 12,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}
        >
          {searchResult.llm_route && (
            <Alert
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
              message={
                <Space wrap>
                  <span>
                    Gemini 意图：
                    {searchResult.llm_route.mode === 'outfit' ? '搭配检索' : '单品检索'}
                  </span>
                  {searchResult.llm_route.gemini_ms != null && (
                    <Tag>{searchResult.llm_route.gemini_ms} ms</Tag>
                  )}
                </Space>
              }
              description={
                <div>
                  <div style={{ marginBottom: 8 }}>
                    {searchResult.llm_route.reason || '—'}
                  </div>
                  {searchResult.llm_route.used_queries?.length ? (
                    <Space direction="vertical" size={4} style={{ width: '100%' }}>
                      {searchResult.llm_route.used_queries.map((u, i) => (
                        <Text key={i} code style={{ fontSize: 12, display: 'block' }}>
                          {u.slot ? `${u.slot} · ` : ''}
                          {u.query}
                        </Text>
                      ))}
                    </Space>
                  ) : null}
                </div>
              }
            />
          )}
          <Row gutter={24}>
            <Col span={6}>
              <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>
                搜索查询
              </Text>
              <Text strong style={{ fontSize: 18 }}>
                {searchResult.query}
              </Text>
            </Col>
            <Col span={6}>
              <Text type="secondary" style={{ display: 'block', marginBottom: 4 }}>
                分词结果
              </Text>
              <Text style={{ fontSize: 14, color: '#1890ff' }}>
                {searchResult.query_tokens.length
                  ? searchResult.query_tokens.join(' / ')
                  : '—'}
              </Text>
            </Col>
            <Col span={6}>
              <Statistic
                title="候选数"
                value={searchResult.candidates}
                suffix={`/ ${searchResult.total_items}`}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="搜索耗时"
                value={searchResult.timing.total_ms}
                suffix="ms"
                prefix={<ClockCircleOutlined />}
              />
              {searchResult.timing.gemini_ms != null && (
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginTop: 4 }}>
                  含 Gemini {searchResult.timing.gemini_ms} ms
                </Text>
              )}
            </Col>
          </Row>
        </Card>
      )}

      {searchResult && searchResult.results.length > 0 && (
        <div className="cw-studio-selection-bar">
          <span>
            已选 {selectedStudioKeys.length} / {MAX_STUDIO_PIECES} 件 · 勾选画廊或下方列表中的服装
          </span>
          <Button
            type="primary"
            className="cw-studio-open-btn"
            icon={<ExperimentOutlined />}
            loading={studioPrefillBusy}
            onClick={() => void openStudioDrawer()}
          >
            AI 试衣 / 生图
          </Button>
          <Button
            type="default"
            disabled={selectedStudioKeys.length === 0}
            onClick={() => setSelectedStudioKeys([])}
          >
            清除选择
          </Button>
        </div>
      )}

      {/* 加载状态 */}
      {loading && (
        <Card>
          <Skeleton active paragraph={{ rows: 4 }} />
        </Card>
      )}

      {/* Image Gallery */}
      {searchResult && searchResult.results.length > 0 && (
        <Card
          title={
            <Space>
              <FireOutlined />
              <Text strong>图片画廊</Text>
            </Space>
          }
          style={{
            marginBottom: 24,
            borderRadius: 12,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}
        >
          <Image.PreviewGroup>
            <Row gutter={[16, 16]}>
              {searchResult.results.slice(0, 12).map((result) => (
                <Col key={studioKey(result)} xs={12} sm={8} md={6} lg={4}>
                  <div className="cw-studio-card-wrap image-card">
                    <div
                      className="cw-studio-card-select"
                      onClick={(e) => e.stopPropagation()}
                      onKeyDown={(e) => e.stopPropagation()}
                    >
                      <Checkbox
                        checked={selectedStudioKeys.includes(studioKey(result))}
                        onChange={() => toggleStudioSelection(result)}
                      />
                    </div>
                    <div
                      style={{
                        cursor: 'pointer',
                        borderRadius: 8,
                        overflow: 'hidden',
                        transition: 'transform 0.3s',
                      }}
                      role="presentation"
                      onClick={() => handleShowDetail(result)}
                    >
                    <Badge.Ribbon
                      text={`#${result.rank}`}
                      color={result.rank <= 3 ? '#e94560' : '#1890ff'}
                    >
                      <Image
                        src={getImageUrl(result.image_url)}
                        alt={result.title}
                        style={{
                          width: '100%',
                          height: 200,
                          objectFit: 'cover',
                        }}
                        preview={{
                          mask: <Text style={{ color: '#fff' }}>查看大图</Text>,
                        }}
                      />
                    </Badge.Ribbon>
                    <div
                      style={{
                        padding: '8px',
                        background: 'rgba(0,0,0,0.7)',
                        color: '#fff',
                        fontSize: 12,
                      }}
                    >
                      <div
                        style={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {result.title}
                      </div>
                      <Space size={4} style={{ marginTop: 4 }}>
                        {result.slot_label && (
                          <Tag
                            color="magenta"
                            style={{ fontSize: 10, padding: '0 4px', margin: 0 }}
                          >
                            {result.slot_label}
                          </Tag>
                        )}
                        <Tag
                          color="blue"
                          style={{ fontSize: 10, padding: '0 4px', margin: 0 }}
                        >
                          {result.category}
                        </Tag>
                        <Tag
                          color={
                            colorMap[result.primary_color] ? undefined : 'default'
                          }
                          style={{
                            fontSize: 10,
                            padding: '0 4px',
                            margin: 0,
                            background: colorMap[result.primary_color],
                            color:
                              result.primary_color === '白色' ? '#000' : '#fff',
                            border: 'none',
                          }}
                        >
                          {result.primary_color}
                        </Tag>
                      </Space>
                    </div>
                    </div>
                  </div>
                </Col>
              ))}
            </Row>
          </Image.PreviewGroup>
        </Card>
      )}

      {/* Details Card List */}
      {searchResult && searchResult.results.length > 0 && (
        <Card
          title={
            <Space>
              <StarOutlined />
              <Text strong>搜索结果详情</Text>
            </Space>
          }
          style={{ borderRadius: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
        >
          <Row gutter={[16, 16]}>
            {searchResult.results.map((result) => (
              <Col key={studioKey(result)} xs={24} sm={24} md={12} lg={12} xl={8}>
                <Card
                  hoverable
                  onClick={() => handleShowDetail(result)}
                  style={{
                    borderRadius: 8,
                    height: '100%',
                  }}
                  bodyStyle={{ padding: 16 }}
                >
                  <div style={{ display: 'flex', gap: 16 }}>
                    <div
                      onClick={(e) => e.stopPropagation()}
                      onKeyDown={(e) => e.stopPropagation()}
                      style={{ flexShrink: 0, paddingTop: 4 }}
                    >
                      <Checkbox
                        checked={selectedStudioKeys.includes(studioKey(result))}
                        onChange={() => toggleStudioSelection(result)}
                      />
                    </div>
                    {/* Rank */}
                    <div
                      style={{
                        width: 60,
                        height: 60,
                        borderRadius: '50%',
                        background:
                          result.rank <= 3
                            ? 'linear-gradient(135deg, #e94560 0%, #ff6b81 100%)'
                            : 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
                        color: '#fff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 24,
                        fontWeight: 'bold',
                        flexShrink: 0,
                      }}
                    >
                      {result.rank}
                    </div>

                    {/* Content */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <Title
                        level={5}
                        style={{
                          margin: 0,
                          marginBottom: 8,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {result.title}
                      </Title>

                      <Space wrap style={{ marginBottom: 12 }}>
                        {result.slot_label && (
                          <Tag color="magenta">{result.slot_label}</Tag>
                        )}
                        <Tag color="blue">{result.category}</Tag>
                        <Tag
                          color={
                            colorMap[result.primary_color] ? undefined : 'default'
                          }
                          style={{
                            background: colorMap[result.primary_color],
                            color:
                              result.primary_color === '白色' ? '#000' : '#fff',
                            border: 'none',
                          }}
                        >
                          {result.primary_color}
                        </Tag>
                        <Tag color="purple">{result.primary_style}</Tag>
                        <Tag color="green">{result.gender}</Tag>
                      </Space>

                      {/* Scores */}
                      <div>
                        {renderScoreProgress(
                          '重排序',
                          result.scores.reranker
                        )}
                        {renderScoreProgress('向量相似度', result.scores.vector_sim)}
                        {renderScoreProgress('BM25', result.scores.bm25)}
                        {renderScoreProgress('RRF 融合', result.scores.rrf)}
                      </div>

                      <div style={{ marginTop: 8 }}>
                        <Badge
                          status="processing"
                          text={`来源：${result.scores.source}`}
                        />
                      </div>
                    </div>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* Empty State */}
      {!loading && !searchResult && (
        <Card style={{ borderRadius: 12, textAlign: 'center', padding: 60 }}>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <span>
                输入关键词开始搜索
              </span>
            }
          />
        </Card>
      )}

      {/* Product Details Drawer */}
      <Drawer
        title="商品详情"
        width={720}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        bodyStyle={{ paddingBottom: 80 }}
      >
        {productLoading ? (
          <Skeleton active paragraph={{ rows: 10 }} />
        ) : selectedProduct ? (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* Title */}
            <Title level={4} style={{ margin: 0 }}>
              {selectedProduct.ecommerce?.title || selectedProduct.basic_info?.category || '-'}
            </Title>

            {/* Basic Info */}
            <Card title="基本信息" size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="品类">
                  {selectedProduct.basic_info?.category || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="子类">
                  {selectedProduct.basic_info?.subcategory || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="性别">
                  {selectedProduct.basic_info?.gender || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="年龄段">
                  {selectedProduct.basic_info?.age_range || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="季节">
                  {Array.isArray(selectedProduct.basic_info?.season) ? selectedProduct.basic_info.season.join(', ') : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="场合">
                  {Array.isArray(selectedProduct.basic_info?.occasion) ? selectedProduct.basic_info.occasion.join(', ') : '-'}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {/* Style */}
            <Card title="风格与审美" size="small">
              <Space wrap style={{ marginBottom: 8 }}>
                <Tag color="purple">{selectedProduct.style?.primary_style || '-'}</Tag>
                {selectedProduct.style?.secondary_styles?.map((s: string, i: number) => (
                  <Tag key={i} color="geekblue">{s}</Tag>
                ))}
                {selectedProduct.style?.aesthetic && <Tag color="magenta">{selectedProduct.style.aesthetic}</Tag>}
              </Space>
              {selectedProduct.style?.trend_relevance && (
                <div style={{ color: '#888', fontSize: 13 }}>{selectedProduct.style.trend_relevance}</div>
              )}
            </Card>

            {/* Colors */}
            <Card title="色彩分析" size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="主色">
                  <Space>
                    <div style={{
                      width: 16, height: 16, borderRadius: 4,
                      background: colorMap[selectedProduct.colors?.primary_color] || '#ccc',
                      border: '1px solid #d9d9d9',
                    }} />
                    {selectedProduct.colors?.primary_color || '-'}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="配色方案">
                  {selectedProduct.colors?.color_scheme || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="色温">
                  {selectedProduct.colors?.color_temperature || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="饱和度">
                  {selectedProduct.colors?.color_saturation || '-'}
                </Descriptions.Item>
              </Descriptions>
              {selectedProduct.colors?.secondary_colors?.length > 0 && (
                <Space wrap style={{ marginTop: 8 }}>
                  <Text type="secondary">辅色：</Text>
                  {selectedProduct.colors.secondary_colors.map((c: string, i: number) => (
                    <Tag key={i}>{c}</Tag>
                  ))}
                </Space>
              )}
            </Card>

            {/* Material */}
            <Card title="面料材质" size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="面料">{selectedProduct.material?.primary_fabric || '-'}</Descriptions.Item>
                <Descriptions.Item label="克重">{selectedProduct.material?.fabric_weight || '-'}</Descriptions.Item>
                <Descriptions.Item label="质感">{selectedProduct.material?.texture || '-'}</Descriptions.Item>
                <Descriptions.Item label="垂感">{selectedProduct.material?.drape || '-'}</Descriptions.Item>
                <Descriptions.Item label="弹性">{selectedProduct.material?.elasticity || '-'}</Descriptions.Item>
                <Descriptions.Item label="透度">{selectedProduct.material?.transparency || '-'}</Descriptions.Item>
              </Descriptions>
            </Card>

            {/* Construction */}
            <Card title="版型与合身" size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="廓形">{selectedProduct.construction?.silhouette || '-'}</Descriptions.Item>
                <Descriptions.Item label="合身度">{selectedProduct.construction?.fit || '-'}</Descriptions.Item>
                <Descriptions.Item label="长度">{selectedProduct.construction?.length || '-'}</Descriptions.Item>
                <Descriptions.Item label="领型">{selectedProduct.construction?.neckline || '-'}</Descriptions.Item>
                <Descriptions.Item label="袖型">{selectedProduct.construction?.sleeve_type || '-'}</Descriptions.Item>
                <Descriptions.Item label="腰线">{selectedProduct.construction?.waistline || '-'}</Descriptions.Item>
              </Descriptions>
            </Card>

            {/* Design Details */}
            <Card title="设计细节" size="small">
              <Descriptions column={1} size="small">
                <Descriptions.Item label="图案">{selectedProduct.design_details?.pattern_type || '-'}</Descriptions.Item>
                {selectedProduct.design_details?.pattern_description && (
                  <Descriptions.Item label="描述">{selectedProduct.design_details.pattern_description}</Descriptions.Item>
                )}
              </Descriptions>
              {selectedProduct.design_details?.decorations?.length > 0 && (
                <Space wrap style={{ marginTop: 8 }}>
                  <Text type="secondary">装饰：</Text>
                  {selectedProduct.design_details.decorations.map((d: string, i: number) => <Tag key={i} color="orange">{d}</Tag>)}
                </Space>
              )}
              {selectedProduct.design_details?.craft_techniques?.length > 0 && (
                <Space wrap style={{ marginTop: 8 }}>
                  <Text type="secondary">工艺：</Text>
                  {selectedProduct.design_details.craft_techniques.map((c: string, i: number) => <Tag key={i} color="cyan">{c}</Tag>)}
                </Space>
              )}
            </Card>

            {/* Visual & Body */}
            <Card title="视觉印象" size="small">
              {selectedProduct.visual_impression?.overall_feel && (
                <div style={{ fontStyle: 'italic', color: '#555', marginBottom: 8 }}>"{selectedProduct.visual_impression.overall_feel}"</div>
              )}
              {selectedProduct.visual_impression?.design_highlight && (
                <Tag color="gold">亮点：{selectedProduct.visual_impression.design_highlight}</Tag>
              )}
            </Card>

            {/* Body Compatibility */}
            {selectedProduct.body_compatibility && (
              <Card title="身材适配" size="small">
                {selectedProduct.body_compatibility.suitable_body_types?.length > 0 && (
                  <Space wrap style={{ marginBottom: 8 }}>
                    {selectedProduct.body_compatibility.suitable_body_types.map((t: string, i: number) => <Tag key={i} color="green">{t}</Tag>)}
                  </Space>
                )}
                {selectedProduct.body_compatibility.flattering_features && (
                  <div style={{ color: '#666', fontSize: 13 }}>{selectedProduct.body_compatibility.flattering_features}</div>
                )}
              </Card>
            )}

            {/* Commercial */}
            <Card title="商业信息" size="small">
              <Descriptions column={1} size="small">
                <Descriptions.Item label="价位档">{selectedProduct.commercial?.price_tier || '-'}</Descriptions.Item>
                <Descriptions.Item label="目标人群">{selectedProduct.commercial?.target_audience || '-'}</Descriptions.Item>
              </Descriptions>
              {selectedProduct.commercial?.selling_points?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary">卖点：</Text>
                  <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                    {selectedProduct.commercial.selling_points.map((sp: string, i: number) => <li key={i}>{sp}</li>)}
                  </ul>
                </div>
              )}
              {selectedProduct.commercial?.coordination_suggestions?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary">搭配建议：</Text>
                  <Timeline style={{ marginTop: 8 }}
                    items={selectedProduct.commercial.coordination_suggestions.map((s: string, i: number) => ({
                      children: s, color: i === 0 ? 'green' : 'blue',
                    }))}
                  />
                </div>
              )}
            </Card>

            {/* E-commerce */}
            <Card title="电商信息" size="small">
              {selectedProduct.ecommerce?.search_keywords?.length > 0 && (
                <Space wrap style={{ marginBottom: 8 }}>
                  {selectedProduct.ecommerce.search_keywords.map((kw: string, i: number) => <Tag key={i} color="blue">{kw}</Tag>)}
                </Space>
              )}
              {selectedProduct.ecommerce?.description && (
                <div style={{ color: '#555', fontSize: 13, marginTop: 8 }}>{selectedProduct.ecommerce.description}</div>
              )}
            </Card>
          </Space>
        ) : null}
      </Drawer>

      <AiStudioDrawer
        open={studioOpen}
        onClose={() => setStudioOpen(false)}
        clothes={studioClothes}
        onClothesChange={(next) => {
          setStudioClothes(next)
          setSelectedStudioKeys(next.map((c) => c.id))
        }}
      />

      <style>{`
        .image-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
      `}</style>
    </div>
  )
}

export default SearchPage
