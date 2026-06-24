import React, { useState, useEffect } from 'react'
import axios from 'axios'
import DataTable from '../components/DataTable'

const Styles = () => {
  const [styles, setStyles] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingStyle, setEditingStyle] = useState(null)
  const [formData, setFormData] = useState({})
  const [categories, setCategories] = useState([])
  const [tones, setTones] = useState([])

  useEffect(() => {
    loadStyles()
    loadOptions()
  }, [])

  const loadOptions = async () => {
    try {
      const [cats, tns] = await Promise.all([
        axios.get('/api/v1/admin/styles/categories'),
        axios.get('/api/v1/admin/styles/tones')
      ])
      setCategories(cats.data.categories)
      setTones(tns.data.tones)
    } catch (error) {
      console.error('Не удалось загрузить опции:', error)
    }
  }

  const loadStyles = async () => {
    try {
      const res = await axios.get('/api/v1/admin/styles')
      setStyles(res.data.styles || [])
      setLoading(false)
    } catch (error) {
      console.error('Не удалось загрузить стили:', error)
      setLoading(false)
    }
  }

  const handleEdit = (style) => {
    setEditingStyle(style)
    setFormData({ ...style })
    setShowForm(true)
  }

  const handleDelete = async (style) => {
    if (window.confirm(`Удалить стиль "${style.name}"?`)) {
      try {
        await axios.delete(`/api/v1/admin/styles/${style.style_id}`)
        loadStyles()
      } catch (error) {
        alert('Не удалось удалить стиль: ' + (error.response?.data?.detail || error.message))
      }
    }
  }

  const handleSubmit = async (data) => {
    try {
      if (editingStyle) {
        await axios.put(`/api/v1/admin/styles/${data.style_id}`, data)
      } else {
        await axios.post('/api/v1/admin/styles', data)
      }
      setShowForm(false)
      setEditingStyle(null)
      setFormData({})
      loadStyles()
    } catch (error) {
      alert('Не удалось сохранить стиль: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handlePreview = async (style) => {
    try {
      const res = await axios.get(`/api/v1/admin/styles/${style.style_id}/preview`)
      const examples = res.data.examples || []
      const examplesText = Array.isArray(examples) 
        ? examples.map(e => `Ввод: ${e.input || ''}\nВывод: ${e.output || ''}`).join('\n')
        : `Примеры не найдены`
      alert(`Стиль: ${res.data.name}\nОписание: ${res.data.description || ''}\nКатегория: ${res.data.category || ''}\nТон: ${res.data.tone || ''}\n\nПримеры:\n${examplesText}`)
    } catch (error) {
      alert('Не удалось предпросмотреть стиль: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleSyncAll = async () => {
    try {
      await axios.post('/api/v1/admin/styles/sync')
      alert('Стили успешно синхронизированы с Qdrant!')
    } catch (error) {
      alert('Ошибка синхронизации стилей: ' + (error.response?.data?.detail || error.message))
    }
  }

  const columns = [
    { key: 'name', label: 'Название' },
    { key: 'category', label: 'Категория' },
    { key: 'tone', label: 'Тон' },
    { key: 'is_active', label: 'Статус' },
    { 
      key: 'actions', 
      label: 'Предпросмотр',
      render: (style) => <button onClick={() => handlePreview(style)} className="btn btn-sm btn-secondary">Предпросмотр</button>
    }
  ]

  if (loading) {
    return <div className="loading">Загрузка стилей...</div>
  }

  return (
    <div className="styles-page">
      <div className="page-header">
        <h1>Художественные стили</h1>
        <div className="header-actions">
          <button onClick={handleSyncAll} className="btn btn-primary">Синхронизировать с Qdrant</button>
          <button onClick={() => { setShowForm(true); setEditingStyle(null); setFormData({}); }} className="btn btn-primary">
            + Добавить стиль
          </button>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={styles}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onRefresh={loadStyles}
      />

      {showForm && (
        <div className="modal">
          <div className="modal-content">
            <h2>{editingStyle ? 'Редактирование стиля' : 'Создание стиля'}</h2>
            <form onSubmit={(e) => { e.preventDefault(); handleSubmit(formData) }}>
              <div className="form-group">
                <label htmlFor="name">Название *</label>
                <input
                  id="name"
                  value={formData.name || ''}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="description">Описание</label>
                <textarea
                  id="description"
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label htmlFor="category">Категория *</label>
                <select
                  id="category"
                  value={formData.category || ''}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  required
                >
                  <option value="">Выберите категорию</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="tone">Тон *</label>
                <select
                  id="tone"
                  value={formData.tone || ''}
                  onChange={(e) => setFormData({ ...formData, tone: e.target.value })}
                  required
                >
                  <option value="">Выберите тон</option>
                  {tones.map(tone => (
                    <option key={tone} value={tone}>{tone}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="examples">Примеры (JSON массив)</label>
                <textarea
                  id="examples"
                  value={JSON.stringify(formData.examples || [], null, 2)}
                  onChange={(e) => {
                    try {
                      setFormData({ ...formData, examples: JSON.parse(e.target.value) })
                    } catch (err) {
                      setFormData({ ...formData, examples: e.target.value })
                    }
                  }}
                  placeholder='[{"input": "...", "output": "...", "note": "..."}]'
                  rows={5}
                />
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active !== false}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  Активно
                </label>
              </div>
              <div className="form-actions">
                <button type="button" onClick={() => setShowForm(false)} className="btn btn-secondary">Отмена</button>
                <button type="submit" className="btn btn-primary">Сохранить</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Styles
