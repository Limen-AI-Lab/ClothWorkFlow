import { useState } from 'react'
import {
  Input,
  Slider,
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
} from 'antd'
import {
  SearchOutlined,
  ClockCircleOutlined,
  FireOutlined,
  StarOutlined,
} from '@ant-design/icons'
import { searchProducts, getProduct, getImageUrl } from '../api'
import type { SearchResponse, SearchResult, ProductResponse } from '../types'

const { Search } = Input
const { Text, Title } = Typography

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

// Quick query examples
const quickQueries = [
  'Slimming summer dress',
  'Streetwear men\'s T-shirt, acid wash',
  'Formal elegant dress for party',
  'Breathable and affordable summer clothes',
  'Warm thick hoodie for winter',
  'Business shirt for work',
  'Photogenic vacation outfit for beach',
  'Oversized trendy streetwear',
]

const SearchPage = () => {
  const [query, setQuery] = useState('')
  const [topN, setTopN] = useState(20)
  const [loading, setLoading] = useState(false)
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<ProductResponse | null>(
    null
  )
  const [productLoading, setProductLoading] = useState(false)

  // Execute search
  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      message.warning('Please enter a search keyword')
      return
    }

    setLoading(true)
    try {
      const result = await searchProducts({
        query: searchQuery,
        top_n: topN,
      })
      setSearchResult(result)
      message.success(`Found ${result.results.length} related products`)
    } catch (error) {
      message.error('Search failed, please check if the backend service is running')
      console.error('Search error:', error)
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
      message.error('Failed to load product details')
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
      {/* Search Bar */}
      <Card
        style={{
          marginBottom: 24,
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={3} style={{ margin: 0, marginBottom: 16 }}>
              <SearchOutlined style={{ marginRight: 8 }} />
              Smart Search
            </Title>
            <Search
              placeholder="Enter product description, e.g., casual style blue T-shirt"
              size="large"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onSearch={handleSearch}
              enterButton="Search"
              loading={loading}
              style={{ fontSize: 16 }}
            />
          </div>

          <div>
            <Text strong>Number of Results: {topN}</Text>
            <Slider
              min={5}
              max={50}
              value={topN}
              onChange={setTopN}
              marks={{ 5: '5', 20: '20', 50: '50' }}
              style={{ marginTop: 8 }}
            />
          </div>

          <div>
            <Text type="secondary" style={{ marginBottom: 8, display: 'block' }}>
              Try these queries:
            </Text>
            <Space wrap>
              {quickQueries.map((q) => (
                <Tag
                  key={q}
                  color="blue"
                  style={{ cursor: 'pointer' }}
                  onClick={() => {
                    setQuery(q)
                    handleSearch(q)
                  }}
                >
                  {q}
                </Tag>
              ))}
            </Space>
          </div>
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
          <Row gutter={24}>
            <Col span={6}>
              <Statistic
                title="Search Query"
                value={searchResult.query}
                valueStyle={{ fontSize: 18 }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Tokenized Result"
                value={searchResult.query_tokens.join(' / ')}
                valueStyle={{ fontSize: 14, color: '#1890ff' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Candidates"
                value={searchResult.candidates}
                suffix={`/ ${searchResult.total_items}`}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Search Time"
                value={searchResult.timing.total_ms}
                suffix="ms"
                prefix={<ClockCircleOutlined />}
              />
            </Col>
          </Row>
        </Card>
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
              <Text strong>Image Gallery</Text>
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
                <Col key={result.rank} xs={12} sm={8} md={6} lg={4}>
                  <div
                    style={{
                      position: 'relative',
                      cursor: 'pointer',
                      borderRadius: 8,
                      overflow: 'hidden',
                      transition: 'transform 0.3s',
                    }}
                    className="image-card"
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
                          mask: <Text style={{ color: '#fff' }}>View Full Size</Text>,
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
              <Text strong>Search Results Details</Text>
            </Space>
          }
          style={{ borderRadius: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
        >
          <Row gutter={[16, 16]}>
            {searchResult.results.map((result) => (
              <Col key={result.rank} xs={24} sm={24} md={12} lg={12} xl={8}>
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
                          'Reranker',
                          result.scores.reranker
                        )}
                        {renderScoreProgress('Vector Similarity', result.scores.vector_sim)}
                        {renderScoreProgress('BM25', result.scores.bm25)}
                        {renderScoreProgress('RRF Fusion', result.scores.rrf)}
                      </div>

                      <div style={{ marginTop: 8 }}>
                        <Badge
                          status="processing"
                          text={`Source: ${result.scores.source}`}
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
                Enter keywords to start searching
                <br />
                or click on the quick query examples above
              </span>
            }
          />
        </Card>
      )}

      {/* Product Details Drawer */}
      <Drawer
        title="Product Details"
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
            <Card title="Basic Info" size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Category">
                  {selectedProduct.basic_info?.category || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="Subcategory">
                  {selectedProduct.basic_info?.subcategory || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="Gender">
                  {selectedProduct.basic_info?.gender || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="Age Range">
                  {selectedProduct.basic_info?.age_range || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="Season">
                  {Array.isArray(selectedProduct.basic_info?.season) ? selectedProduct.basic_info.season.join(', ') : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="Occasion">
                  {Array.isArray(selectedProduct.basic_info?.occasion) ? selectedProduct.basic_info.occasion.join(', ') : '-'}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {/* Style */}
            <Card title="Style & Aesthetic" size="small">
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
            <Card title="Color Analysis" size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Primary Color">
                  <Space>
                    <div style={{
                      width: 16, height: 16, borderRadius: 4,
                      background: colorMap[selectedProduct.colors?.primary_color] || '#ccc',
                      border: '1px solid #d9d9d9',
                    }} />
                    {selectedProduct.colors?.primary_color || '-'}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="Color Scheme">
                  {selectedProduct.colors?.color_scheme || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="Temperature">
                  {selectedProduct.colors?.color_temperature || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="Saturation">
                  {selectedProduct.colors?.color_saturation || '-'}
                </Descriptions.Item>
              </Descriptions>
              {selectedProduct.colors?.secondary_colors?.length > 0 && (
                <Space wrap style={{ marginTop: 8 }}>
                  <Text type="secondary">Secondary:</Text>
                  {selectedProduct.colors.secondary_colors.map((c: string, i: number) => (
                    <Tag key={i}>{c}</Tag>
                  ))}
                </Space>
              )}
            </Card>

            {/* Material */}
            <Card title="Material & Fabric" size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Fabric">{selectedProduct.material?.primary_fabric || '-'}</Descriptions.Item>
                <Descriptions.Item label="Weight">{selectedProduct.material?.fabric_weight || '-'}</Descriptions.Item>
                <Descriptions.Item label="Texture">{selectedProduct.material?.texture || '-'}</Descriptions.Item>
                <Descriptions.Item label="Drape">{selectedProduct.material?.drape || '-'}</Descriptions.Item>
                <Descriptions.Item label="Elasticity">{selectedProduct.material?.elasticity || '-'}</Descriptions.Item>
                <Descriptions.Item label="Transparency">{selectedProduct.material?.transparency || '-'}</Descriptions.Item>
              </Descriptions>
            </Card>

            {/* Construction */}
            <Card title="Construction & Fit" size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Silhouette">{selectedProduct.construction?.silhouette || '-'}</Descriptions.Item>
                <Descriptions.Item label="Fit">{selectedProduct.construction?.fit || '-'}</Descriptions.Item>
                <Descriptions.Item label="Length">{selectedProduct.construction?.length || '-'}</Descriptions.Item>
                <Descriptions.Item label="Neckline">{selectedProduct.construction?.neckline || '-'}</Descriptions.Item>
                <Descriptions.Item label="Sleeve">{selectedProduct.construction?.sleeve_type || '-'}</Descriptions.Item>
                <Descriptions.Item label="Waistline">{selectedProduct.construction?.waistline || '-'}</Descriptions.Item>
              </Descriptions>
            </Card>

            {/* Design Details */}
            <Card title="Design Details" size="small">
              <Descriptions column={1} size="small">
                <Descriptions.Item label="Pattern">{selectedProduct.design_details?.pattern_type || '-'}</Descriptions.Item>
                {selectedProduct.design_details?.pattern_description && (
                  <Descriptions.Item label="Description">{selectedProduct.design_details.pattern_description}</Descriptions.Item>
                )}
              </Descriptions>
              {selectedProduct.design_details?.decorations?.length > 0 && (
                <Space wrap style={{ marginTop: 8 }}>
                  <Text type="secondary">Decorations:</Text>
                  {selectedProduct.design_details.decorations.map((d: string, i: number) => <Tag key={i} color="orange">{d}</Tag>)}
                </Space>
              )}
              {selectedProduct.design_details?.craft_techniques?.length > 0 && (
                <Space wrap style={{ marginTop: 8 }}>
                  <Text type="secondary">Craft:</Text>
                  {selectedProduct.design_details.craft_techniques.map((c: string, i: number) => <Tag key={i} color="cyan">{c}</Tag>)}
                </Space>
              )}
            </Card>

            {/* Visual & Body */}
            <Card title="Visual Impression" size="small">
              {selectedProduct.visual_impression?.overall_feel && (
                <div style={{ fontStyle: 'italic', color: '#555', marginBottom: 8 }}>"{selectedProduct.visual_impression.overall_feel}"</div>
              )}
              {selectedProduct.visual_impression?.design_highlight && (
                <Tag color="gold">Highlight: {selectedProduct.visual_impression.design_highlight}</Tag>
              )}
            </Card>

            {/* Body Compatibility */}
            {selectedProduct.body_compatibility && (
              <Card title="Body Compatibility" size="small">
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
            <Card title="Commercial Info" size="small">
              <Descriptions column={1} size="small">
                <Descriptions.Item label="Price Tier">{selectedProduct.commercial?.price_tier || '-'}</Descriptions.Item>
                <Descriptions.Item label="Target Audience">{selectedProduct.commercial?.target_audience || '-'}</Descriptions.Item>
              </Descriptions>
              {selectedProduct.commercial?.selling_points?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary">Selling Points:</Text>
                  <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                    {selectedProduct.commercial.selling_points.map((sp: string, i: number) => <li key={i}>{sp}</li>)}
                  </ul>
                </div>
              )}
              {selectedProduct.commercial?.coordination_suggestions?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary">Styling Suggestions:</Text>
                  <Timeline style={{ marginTop: 8 }}
                    items={selectedProduct.commercial.coordination_suggestions.map((s: string, i: number) => ({
                      children: s, color: i === 0 ? 'green' : 'blue',
                    }))}
                  />
                </div>
              )}
            </Card>

            {/* E-commerce */}
            <Card title="E-commerce Info" size="small">
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
