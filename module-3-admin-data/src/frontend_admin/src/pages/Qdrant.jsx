import React, { useState, useEffect } from 'react'
import axios from 'axios'
import DataTable from '../components/DataTable'

const Qdrant = () => {
  const [activeTab, setActiveTab] = useState('collections')
  const [collections, setCollections] = useState([])
  const [collectionInfo, setCollectionInfo] = useState(null)
  const [profiles, setProfiles] = useState([])
  const [rules, setRules] = useState([])
  const [styles, setStyles] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedCollection, setSelectedCollection] = useState('corporate_rules')
  const [qdrantStatus, setQdrantStatus] = useState({})

  useEffect(() => {
    loadCollections()
    loadQdrantStatus()
  }, [])

  const loadQdrantStatus = async () => {
    try {
      const res = await axios.get('/api/v1/admin/system/status')
      setQdrantStatus(res.data)
    } catch (error) {
      console.error('Failed to load Qdrant status:', error)
    }
  }

  const loadCollections = async () => {
    try {
      const res = await axios.get('/api/v1/admin/system/qdrant/collections')
      setCollections(res.data.collections || [])
      setLoading(false)
    } catch (error) {
      console.error('Failed to load collections:', error)
      setLoading(false)
    }
  }

  const loadCollectionInfo = async (collectionName) => {
    try {
      const res = await axios.get(`/api/v1/admin/system/qdrant/collections/${collectionName}/info`)
      setCollectionInfo(res.data)
    } catch (error) {
      console.error(`Failed to load collection info for ${collectionName}:`, error)
    }
  }

  const loadProfiles = async () => {
    try {
      const res = await axios.get('/api/v1/admin/system/qdrant/profiles')
      setProfiles(res.data.profiles || [])
    } catch (error) {
      console.error('Failed to load profiles:', error)
    }
  }

  const loadRules = async () => {
    try {
      const res = await axios.get('/api/v1/admin/system/qdrant/rules')
      setRules(res.data.rules || [])
    } catch (error) {
      console.error('Failed to load rules:', error)
    }
  }

  const loadStyles = async () => {
    try {
      const res = await axios.get('/api/v1/admin/system/qdrant/styles')
      setStyles(res.data.styles || [])
    } catch (error) {
      console.error('Failed to load styles:', error)
    }
  }

  const syncAllProfiles = async () => {
    try {
      await axios.post('/api/v1/admin/profiles/sync')
      await loadProfiles()
      alert('Профили успешно синхронизированы')
    } catch (error) {
      console.error('Failed to sync profiles:', error)
      alert('Ошибка при синхронизации профилей')
    }
  }

  const syncAllRules = async () => {
    try {
      await axios.post('/api/v1/admin/rules/sync')
      await loadRules()
      alert('Правила успешно синхронизированы')
    } catch (error) {
      console.error('Failed to sync rules:', error)
      alert('Ошибка при синхронизации правил')
    }
  }

  const syncAllStyles = async () => {
    try {
      await axios.post('/api/v1/admin/styles/sync')
      await loadStyles()
      alert('Стили успешно синхронизированы')
    } catch (error) {
      console.error('Failed to sync styles:', error)
      alert('Ошибка при синхронизации стилей')
    }
  }

  const handleCollectionClick = (collection) => {
    setSelectedCollection(collection.name)
    loadCollectionInfo(collection.name)
  }

  // Tabs configuration
  const tabs = [
    { id: 'collections', label: 'Коллекции' },
    { id: 'profiles', label: 'Профили' },
    { id: 'rules', label: 'Правила' },
    { id: 'styles', label: 'Стили' }
  ]

  // Helper function to display safe values
  const displayValue = (value, defaultValue = 'N/A') => {
    if (value === null || value === undefined || value === '') {
      return defaultValue
    }
    if (typeof value === 'object' && Object.keys(value).length === 0) {
      return defaultValue
    }
    return value
  }

  if (loading && activeTab === 'collections') {
    return <div className="loading">Загрузка коллекций Qdrant...</div>
  }

  return (
    <div className="qdrant-page">
      <div className="page-header">
        <h1>Qdrant (Module 1)</h1>
        <div className="header-actions">
          <span className={`status-badge ${qdrantStatus.system === 'healthy' ? 'healthy' : 'unhealthy'}`}>
            {qdrantStatus.system === 'healthy' ? '✓ Qdrant OK' : '⚠ Qdrant issue'}
          </span>
        </div>
      </div>

      <div className="tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="tab-content">
        {activeTab === 'collections' && (
          <div className="collections-view">
            <h2>Коллекции Qdrant</h2>
            <div className="collections-grid">
              {collections.length > 0 ? (
                collections.map((collection, idx) => (
                  <div 
                    key={idx} 
                    className="collection-card"
                    onClick={() => handleCollectionClick(collection)}
                  >
                    <h3>{displayValue(collection.name, 'Unknown')}</h3>
                    <p className="collection-desc">{displayValue(collection.description, 'No description')}</p>
                    <button className="btn btn-sm btn-secondary">View Details</button>
                  </div>
                ))
              ) : (
                <p className="no-data">Нет коллекций в Qdrant</p>
              )}
            </div>

            {collectionInfo && (
              <div className="collection-details">
                <h2>Детали: {displayValue(collectionInfo.collection, 'Unknown')}</h2>
                <p className="info-item"><strong>Количество документов:</strong> {displayValue(collectionInfo.count, 0)}</p>
                
                {collectionInfo.documents && collectionInfo.documents.length > 0 ? (
                  <div className="documents-preview">
                    <h3>Документы (первые {Math.min(collectionInfo.documents.length, 10)}):</h3>
                    <DataTable 
                      columns={[
                        { key: 'document_id', label: 'Document ID', width: '200px' },
                        { key: 'filename', label: 'Filename', width: '150px' },
                        { key: 'file_type', label: 'Type', width: '80px' },
                        { key: 'file_size', label: 'Size', width: '80px' },
                        { key: 'status', label: 'Status', width: '80px' }
                      ]}
                      data={collectionInfo.documents}
                      getRowKey={(row) => row.document_id}
                      formatDate={(value) => value}
                      formatSize={(value) => value ? `${(value / 1024).toFixed(2)} KB` : '0 KB'}
                      formatStatus={(value) => value}
                    />
                  </div>
                ) : (
                  <div className="documents-preview">
                    <h3>Документы:</h3>
                    <p className="no-data">Нет документов в этой коллекции</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'profiles' && (
          <div className="profiles-view">
            <div className="action-bar">
              <h2>Профили пользователей (user_profiles)</h2>
              <button onClick={syncAllProfiles} className="btn btn-primary">Синхронизировать с PostgreSQL</button>
              <button onClick={loadProfiles} className="btn btn-secondary">Обновить</button>
            </div>
            {profiles.length > 0 ? (
              <DataTable 
                columns={[
                  { key: 'user_id', label: 'User ID', width: '120px' },
                  { key: 'full_name', label: 'Full Name', width: '200px' },
                  { key: 'role', label: 'Role', width: '100px' },
                  { key: 'department', label: 'Department', width: '120px' },
                  { key: 'communication_mode', label: 'Mode', width: '80px' },
                  { key: 'honorific_type', label: 'Honorific', width: '100px' }
                ]}
                data={profiles}
                getRowKey={(row) => row.user_id}
                formatDate={(value) => value}
              />
            ) : (
              <p className="no-data">Нет профилей в Qdrant</p>
            )}
          </div>
        )}

        {activeTab === 'rules' && (
          <div className="rules-view">
            <div className="action-bar">
              <h2>Корпоративные правила (corporate_rules)</h2>
              <button onClick={syncAllRules} className="btn btn-primary">Синхронизировать с PostgreSQL</button>
              <button onClick={loadRules} className="btn btn-secondary">Обновить</button>
            </div>
            {rules.length > 0 ? (
              <DataTable 
                columns={[
                  { key: 'rule_id', label: 'Rule ID', width: '150px' },
                  { key: 'transformation', label: 'Transformation', width: '250px' },
                  { key: 'category', label: 'Category', width: '100px' },
                  { key: 'priority', label: 'Priority', width: '80px' },
                  { key: 'is_active', label: 'Active', width: '70px', render: (row) => row.is_active ? 'Да' : 'Нет' }
                ]}
                data={rules}
                getRowKey={(row) => row.rule_id}
                formatBoolean={(value) => value ? 'Да' : 'Нет'}
                formatSize={(value) => value ? `${(value / 1024).toFixed(2)} KB` : '0 KB'}
              />
            ) : (
              <p className="no-data">Нет правил в Qdrant</p>
            )}
          </div>
        )}

        {activeTab === 'styles' && (
          <div className="styles-view">
            <h2>Художественные стили</h2>
            <button onClick={loadStyles} className="btn btn-secondary">Обновить</button>
            {styles.length > 0 ? (
              <DataTable 
                columns={[
                  { key: 'style_id', label: 'Style ID', width: '180px' },
                  { key: 'is_active', label: 'Активно', width: '70px', render: (row) => row.is_active ? 'Да' : 'Нет' },
                  { key: 'created_at', label: 'Создано', width: '120px' },
                  { key: 'updated_at', label: 'Обновлено', width: '120px' },
                  { key: 'examples', label: 'Примеры', width: '80px', render: (row) => row.examples ? row.examples.length : 0 }
                ]}
                data={styles}
                getRowKey={(row) => row.style_id}
                formatBoolean={(value) => value ? 'Да' : 'Нет'}
                formatSize={(value) => value ? `${(value / 1024).toFixed(2)} KB` : '0 KB'}
                formatDate={(value) => value ? new Date(value).toLocaleString('ru-RU') : '-'}
              />
            ) : (
              <p className="no-data">Нет стилей в Qdrant</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default Qdrant
