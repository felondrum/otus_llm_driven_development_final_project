import React, { useState, useEffect } from 'react'
import axios from 'axios'

const System = () => {
  const [status, setStatus] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStatus()
    const interval = setInterval(loadStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadStatus = async () => {
    try {
      const res = await axios.get('/api/v1/admin/system/status')
      setStatus(res.data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load status:', error)
    }
  }

  const handleClearCache = async () => {
    try {
      await axios.post('/api/v1/admin/system/cache/clear')
      alert('Cache cleared!')
    } catch (error) {
      alert('Failed to clear cache: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleReloadRules = async () => {
    try {
      await axios.post('/api/v1/admin/system/rules/reload')
      alert('Rules reloaded!')
    } catch (error) {
      alert('Failed to reload rules: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleReloadStyles = async () => {
    try {
      await axios.post('/api/v1/admin/system/styles/reload')
      alert('Styles reloaded!')
    } catch (error) {
      alert('Failed to reload styles: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleReindexDocs = async () => {
    try {
      await axios.post('/api/v1/admin/system/documents/reindex')
      alert('Document reindexing started!')
    } catch (error) {
      alert('Failed to reindex documents: ' + (error.response?.data?.detail || error.message))
    }
  }

  const getServiceStatusClass = (service) => {
    if (!service) return 'unknown'
    return service.status === 'healthy' ? 'healthy' : 'unhealthy'
  }

  if (loading) {
    return <div className="loading">Loading system status...</div>
  }

  return (
    <div className="system-page">
      <h1>System Management</h1>

      <div className="system-status">
        <h2>Service Status</h2>
        <div className="status-grid">
          {Object.entries(status.services || {}).map(([name, service]) => (
            <div key={name} className={`status-card ${getServiceStatusClass(service)}`}>
              <h3>{name}</h3>
              <div className="status-badge">{service.status}</div>
              {service.type && <p>Protocol: {service.type}</p>}
              {service.error && <p className="error">Error: {service.error}</p>}
            </div>
          ))}
        </div>
        <div className="system-status-badge">{status.system}</div>
      </div>

      <div className="actions-panel">
        <h2>Actions</h2>
        <div className="actions-grid">
          <button onClick={handleClearCache} className="btn btn-secondary">
            Clear Cache
          </button>
          <button onClick={handleReloadRules} className="btn btn-secondary">
            Reload Rules
          </button>
          <button onClick={handleReloadStyles} className="btn btn-secondary">
            Reload Styles
          </button>
          <button onClick={handleReindexDocs} className="btn btn-secondary">
            Reindex Documents
          </button>
        </div>
      </div>

      <div className="api-info">
        <h2>API Configuration</h2>
        <div className="config-list">
          <div className="config-item">
            <strong>Admin API Port:</strong> 8100
          </div>
          <div className="config-item">
            <strong>Core Engine HTTP:</strong> localhost:8001
          </div>
          <div className="config-item">
            <strong>Chat Frontend:</strong> localhost:8080
          </div>
        </div>
      </div>
    </div>
  )
}

export default System
