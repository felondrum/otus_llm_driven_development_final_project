import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'

const Dashboard = () => {
  const [stats, setStats] = useState({
    profiles: 0,
    chat_profiles: 0,
    rules: 0,
    styles: 0,
    documents: 0,
    qdrant_collections: 0
  })
  const [status, setStatus] = useState({})
  const [qdrantStatus, setQdrantStatus] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
    loadStatus()
    loadQdrantStatus()
  }, [])

  const loadStats = async () => {
    try {
      const [profilesRes, chatProfilesRes, rulesRes, stylesRes, docsRes, qdrantCollectionsRes] = await Promise.all([
        axios.get('/api/v1/admin/profiles'),
        axios.get('/api/v1/admin/chat_profiles'),
        axios.get('/api/v1/admin/rules'),
        axios.get('/api/v1/admin/styles'),
        axios.get('/api/v1/admin/documents'),
        axios.get('/api/v1/admin/system/qdrant/collections').catch(() => null)
      ])
      
      setStats({
        profiles: profilesRes.data.count || 0,
        chat_profiles: chatProfilesRes.data.count || 0,
        rules: rulesRes.data.count || 0,
        styles: stylesRes.data.count || 0,
        documents: docsRes.data.count || 0,
        qdrant_collections: qdrantCollectionsRes?.data.collections?.length || 0
      })
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const loadStatus = async () => {
    try {
      const res = await axios.get('/api/v1/admin/system/status')
      setStatus(res.data)
    } catch (error) {
      console.error('Failed to load status:', error)
    }
  }

  const loadQdrantStatus = async () => {
    try {
      const res = await axios.get('/api/v1/admin/system/qdrant/collections')
      setQdrantStatus(res.data)
    } catch (error) {
      console.error('Failed to load Qdrant status:', error)
    }
  }

  const handleSyncProfiles = async () => {
    try {
      await axios.post('/api/v1/admin/system/profiles/sync')
      alert('Profile sync started!')
    } catch (error) {
      alert('Failed to sync profiles: ' + (error.response?.data?.detail || error.message))
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

  const handleViewQdrant = () => {
    window.location.href = '/qdrant'
  }

  return (
    <div className="dashboard">
      <h1>Admin Dashboard</h1>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Profiles</h3>
          <p className="stat-value">{stats.profiles}</p>
          <Link to="/profiles" className="btn btn-sm btn-secondary">Manage</Link>
        </div>
        <div className="stat-card">
          <h3>Chat Profiles</h3>
          <p className="stat-value">{stats.chat_profiles}</p>
          <Link to="/chat_profiles" className="btn btn-sm btn-secondary">Manage</Link>
        </div>
        <div className="stat-card">
          <h3>Rules</h3>
          <p className="stat-value">{stats.rules}</p>
          <Link to="/rules" className="btn btn-sm btn-secondary">Manage</Link>
        </div>
        <div className="stat-card">
          <h3>Styles</h3>
          <p className="stat-value">{stats.styles}</p>
          <Link to="/styles" className="btn btn-sm btn-secondary">Manage</Link>
        </div>
        <div className="stat-card">
          <h3>Documents</h3>
          <p className="stat-value">{stats.documents}</p>
          <Link to="/documents" className="btn btn-sm btn-secondary">Manage</Link>
        </div>
        <div className="stat-card">
          <h3>Qdrant Collections</h3>
          <p className="stat-value">{stats.qdrant_collections}</p>
          <button onClick={handleViewQdrant} className="btn btn-sm btn-secondary">View</button>
        </div>
      </div>

      <div className="actions-panel">
        <h2>Quick Actions</h2>
        <div className="actions-grid">
          <button onClick={handleSyncProfiles} className="btn btn-primary">
            Sync Profiles
          </button>
          <button onClick={handleClearCache} className="btn btn-secondary">
            Clear Cache
          </button>
          <button onClick={handleReloadRules} className="btn btn-secondary">
            Reload Rules
          </button>
        </div>
      </div>

      {status.system && (
        <div className="system-status">
          <h2>System Status</h2>
          <div className="status-list">
            {Object.entries(status.services || {}).map(([name, service]) => (
              <div key={name} className="status-item">
                <span className="service-name">{name}</span>
                <span className={`status-badge ${service.status}`}>
                  {service.status}
                </span>
                {service.error && (
                  <span className="error-text">{service.error}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
