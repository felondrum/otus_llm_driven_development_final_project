import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import DataTable from '../components/DataTable'

const Rules = () => {
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingRule, setEditingRule] = useState(null)
  const [formData, setFormData] = useState({})
  const [categories, setCategories] = useState([])
  const [roles, setRoles] = useState([])
  const [priorities, setPriorities] = useState([])

  useEffect(() => {
    loadRules()
    loadOptions()
  }, [])

  const loadOptions = async () => {
    try {
      const [cats, rls, pris] = await Promise.all([
        axios.get('/api/v1/admin/rules/categories'),
        axios.get('/api/v1/admin/rules/roles'),
        axios.get('/api/v1/admin/rules/priorities')
      ])
      setCategories(cats.data.categories)
      setRoles(rls.data.roles)
      setPriorities(pris.data.priorities)
    } catch (error) {
      console.error('Failed to load options:', error)
    }
  }

  const loadRules = async () => {
    try {
      const res = await axios.get('/api/v1/admin/rules')
      setRules(res.data.rules || [])
      setLoading(false)
    } catch (error) {
      console.error('Failed to load rules:', error)
      setLoading(false)
    }
  }

  const handleSyncAll = async () => {
    try {
      await axios.post('/api/v1/admin/rules/sync')
      alert('Правила успешно синхронизированы с Qdrant!')
    } catch (error) {
      alert('Ошибка синхронизации правил: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleEdit = (rule) => {
    setEditingRule(rule)
    setFormData({ ...rule })
    setShowForm(true)
  }

  const handleDelete = async (rule) => {
    if (window.confirm(`Удалить правило "${rule.name}"?`)) {
      try {
        await axios.delete(`/api/v1/admin/rules/${rule.rule_id}`)
        loadRules()
      } catch (error) {
        alert('Ошибка удаления правила: ' + (error.response?.data?.detail || error.message))
      }
    }
  }

  const handleReload = async () => {
    try {
      await axios.post('/api/v1/admin/rules/reload')
      alert('Правила перезагружены!')
    } catch (error) {
      alert('Ошибка перезагрузки правил: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleSubmit = async (data) => {
    try {
      if (editingRule) {
        await axios.put(`/api/v1/admin/rules/${data.rule_id}`, data)
      } else {
        await axios.post('/api/v1/admin/rules', data)
      }
      setShowForm(false)
      setEditingRule(null)
      setFormData({})
      loadRules()
    } catch (error) {
      alert('Ошибка сохранения правила: ' + (error.response?.data?.detail || error.message))
    }
  }

  const columns = [
    { key: 'name', label: 'Название' },
    { key: 'category', label: 'Категория' },
    { key: 'role', label: 'Роль' },
    { key: 'priority', label: 'Приоритет' },
    { key: 'is_active', label: 'Статус' }
  ]

  if (loading) {
    return <div className="loading">Загрузка правил...</div>
  }

  return (
    <div className="rules-page">
      <div className="page-header">
        <h1>Корпоративные правила</h1>
        <div className="header-actions">
          <button onClick={handleSyncAll} className="btn btn-primary">Синхронизировать с Qdrant</button>
          <button onClick={handleReload} className="btn btn-secondary">Перезагрузить</button>
          <button onClick={() => { setShowForm(true); setEditingRule(null); setFormData({}); }} className="btn btn-primary">
            + Добавить правило
          </button>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={rules}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onRefresh={loadRules}
      />

      {showForm && (
        <div className="modal">
          <div className="modal-content">
            <h2>{editingRule ? 'Редактирование правила' : 'Создание правила'}</h2>
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
                <label htmlFor="category">Category *</label>
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
                <label htmlFor="role">Роль *</label>
                <select
                  id="role"
                  value={formData.role || ''}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  required
                >
                  <option value="">Выберите роль</option>
                  {roles.map(role => (
                    <option key={role} value={role}>{role}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="priority">Приоритет *</label>
                <select
                  id="priority"
                  value={formData.priority || ''}
                  onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                  required
                >
                  <option value="">Выберите приоритет</option>
                  {priorities.map(pri => (
                    <option key={pri.level} value={pri.level}>{pri.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="condition">Условие *</label>
                <textarea
                  id="condition"
                  value={formData.condition || ''}
                  onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
                  placeholder="если возраст пользователя > 18..."
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="action">Действие *</label>
                <textarea
                  id="action"
                  value={formData.action || ''}
                  onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                  placeholder="возврат ответа..."
                  required
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

export default Rules
