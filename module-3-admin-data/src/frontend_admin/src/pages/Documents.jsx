import React, { useState, useEffect } from 'react'
import axios from 'axios'
import DataTable from '../components/DataTable'

const Documents = () => {
  const [documents, setDocuments] = useState([])
  const [collections, setCollections] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [selectedCollection, setSelectedCollection] = useState('corporate_rules')
  const [editingDoc, setEditingDoc] = useState(null)
  const [editContent, setEditContent] = useState('')
  const [showEditModal, setShowEditModal] = useState(false)

  useEffect(() => {
    loadDocuments()
    loadCollections()
  }, [])

  const loadCollections = async () => {
    try {
      const res = await axios.get('/api/v1/admin/documents/collections')
      setCollections(res.data.collections)
    } catch (error) {
      console.error('Не удалось загрузить коллекции:', error)
    }
  }

  const loadDocuments = async () => {
    try {
      const res = await axios.get('/api/v1/admin/documents', {
        params: { collection: selectedCollection }
      })
      setDocuments(res.data.documents || [])
      setLoading(false)
    } catch (error) {
      console.error('Не удалось загрузить документы:', error)
      setLoading(false)
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setUploading(true)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('collection', selectedCollection)

      await axios.post('/api/v1/admin/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      setSelectedFile(null)
      loadDocuments()
    } catch (error) {
      alert('Не удалось загрузить документ: ' + (error.response?.data?.detail || error.message))
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (docId) => {
    if (window.confirm('Удалить этот документ?')) {
      try {
        await axios.delete(`/api/v1/admin/documents/${docId}`, {
          params: { collection: selectedCollection }
        })
        loadDocuments()
      } catch (error) {
        alert('Не удалось удалить документ: ' + (error.response?.data?.detail || error.message))
      }
    }
  }

  const handleEdit = async (doc) => {
    // Проверяем, что файл текстовый (txt, md, json)
    const textExtensions = ['.txt', '.md', '.json', '.csv', '.xml']
    const hasTextExtension = textExtensions.some(ext => doc.filename.toLowerCase().endsWith(ext))
    
    if (!hasTextExtension) {
      alert('Редактирование доступно только для текстовых файлов (txt, md, json, csv, xml)')
      return
    }
    
    try {
      const res = await axios.get(`/api/v1/admin/documents/${doc.document_id}`, {
        params: { collection: selectedCollection }
      })
      setEditingDoc(doc)
      setEditContent(res.data.data?.content || '')
      setShowEditModal(true)
    } catch (error) {
      alert('Не удалось загрузить содержимое документа: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleSaveEdit = async () => {
    if (!editingDoc || !editContent) return

    try {
      await axios.put(`/api/v1/admin/documents/${editingDoc.document_id}`, {
        content: editContent,
        file_size: new Blob([editContent]).size,
        status: 'updated'
      }, {
        params: { collection: selectedCollection }
      })
      
      setShowEditModal(false)
      setEditingDoc(null)
      setEditContent('')
      loadDocuments()
    } catch (error) {
      alert('Не удалось сохранить изменения: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleSync = async (docId) => {
    try {
      await axios.post(`/api/v1/admin/documents/${docId}/sync`, {}, {
        params: { collection: selectedCollection }
      })
      alert('Документ успешно синхронизирован с Qdrant')
    } catch (error) {
      alert('Не удалось синхронизировать документ: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleSyncAll = async () => {
    if (!window.confirm('Синхронизировать все документы в коллекции с Qdrant?')) return
    
    try {
      await axios.post(`/api/v1/admin/documents/sync`, {}, {
        params: { collection: selectedCollection }
      })
      alert('Все документы успешно синхронизированы')
      loadDocuments()
    } catch (error) {
      alert('Не удалось синхронизировать документы: ' + (error.response?.data?.detail || error.message))
    }
  }

  const columns = [
    { key: 'filename', label: 'Имя файла' },
    { key: 'file_type', label: 'Тип' },
    { 
      key: 'file_size', 
      label: 'Размер', 
      render: (doc) => `${(doc.file_size / 1024).toFixed(2)} КБ` 
    },
    { key: 'status', label: 'Статус' },
    { 
      key: 'actions', 
      label: 'Действия',
      render: (doc) => {
        const textExtensions = ['.txt', '.md', '.json', '.csv', '.xml']
        const hasTextExtension = textExtensions.some(ext => doc.filename.toLowerCase().endsWith(ext))
        
        return (
          <div className="action-buttons">
            <button 
              onClick={() => handleSync(doc.document_id)} 
              className="btn btn-sm btn-secondary"
              title="Синхронизировать с Qdrant"
            >
              Синхронизировать
            </button>
            {hasTextExtension && (
              <button 
                onClick={() => handleEdit(doc)} 
                className="btn btn-sm btn-secondary"
                title="Редактировать текстовый файл"
              >
                Редактировать
              </button>
            )}
            <button 
              onClick={() => handleDelete(doc.document_id)} 
              className="btn btn-sm btn-danger"
            >
              Удалить
            </button>
          </div>
        )
      }
    }
  ]

  if (loading) {
    return <div className="loading">Загрузка документов...</div>
  }

  return (
    <div className="documents-page">
      <div className="page-header">
        <h1>Документы</h1>
        <div className="header-actions">
          <select
            value={selectedCollection}
            onChange={(e) => { setSelectedCollection(e.target.value); loadDocuments() }}
            className="form-control"
          >
            {collections.map(col => (
              <option key={col.name} value={col.name}>{col.name} - {col.description}</option>
            ))}
          </select>
          <button onClick={handleSyncAll} className="btn btn-secondary">Синхронизировать все</button>
          <button onClick={() => loadDocuments()} className="btn btn-secondary">Обновить</button>
        </div>
      </div>

      <div className="upload-section">
        <h2>Загрузка документа</h2>
        <div className="upload-form">
          <input
            type="file"
            onChange={handleFileChange}
            disabled={uploading}
          />
          <button onClick={handleUpload} disabled={!selectedFile || uploading} className="btn btn-primary">
            {uploading ? 'Загрузка...' : 'Загрузить'}
          </button>
        </div>
        {selectedFile && <div className="file-info">Выбрано: {selectedFile.name}</div>}
      </div>

      <DataTable
        columns={columns}
        data={documents}
        onRefresh={loadDocuments}
      />

      {/* Модальное окно редактирования */}
      {showEditModal && editingDoc && (
        <div className="modal">
          <div className="modal-content">
            <h2>Редактирование: {editingDoc.filename}</h2>
            <p className="doc-info">
              Тип: {editingDoc.file_type} | 
              Размер: {(editingDoc.file_size / 1024).toFixed(2)} КБ
            </p>
            <div className="form-group">
              <label htmlFor="edit-content">Содержимое файла</label>
              <textarea
                id="edit-content"
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                placeholder="Введите содержимое файла..."
                style={{
                  fontFamily: 'monospace',
                  fontSize: '14px',
                  minHeight: '300px',
                  padding: '10px',
                  resize: 'vertical'
                }}
              />
            </div>
            <div className="form-actions">
              <button type="button" onClick={() => setShowEditModal(false)} className="btn btn-secondary">Отмена</button>
              <button type="button" onClick={handleSaveEdit} className="btn btn-primary">Сохранить</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Documents
