import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import DataTable from '../components/DataTable'

const ChatProfiles = () => {
  const [profiles, setProfiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingProfile, setEditingProfile] = useState(null)
  const [formData, setFormData] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    loadChatProfiles()
  }, [])

  const loadChatProfiles = async () => {
    try {
      const res = await axios.get('/api/v1/admin/chat_profiles')
      setProfiles(res.data.chat_profiles || [])
      setLoading(false)
    } catch (error) {
      console.error('Failed to load chat profiles:', error)
      setLoading(false)
    }
  }

  const handleEdit = (profile) => {
    setEditingProfile(profile)
    setFormData({ ...profile })
    setShowForm(true)
  }

  const handleDelete = async (profile) => {
    if (window.confirm(`Delete chat profile ${profile.user_id}?`)) {
      try {
        await axios.delete(`/api/v1/admin/chat_profiles/${profile.user_id}`)
        loadChatProfiles()
      } catch (error) {
        alert('Failed to delete chat profile: ' + (error.response?.data?.detail || error.message))
      }
    }
  }

  const handleSyncAll = async () => {
    try {
      await axios.post('/api/v1/admin/chat_profiles/sync')
      alert('All chat profiles sync started!')
    } catch (error) {
      alert('Failed to sync chat profiles: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleSubmit = async (data) => {
    try {
      // Remove empty core_user_id to avoid foreign key error
      const submitData = { ...data }
      if (!submitData.core_user_id || submitData.core_user_id.trim() === '') {
        submitData.core_user_id = null
      }
      
      if (editingProfile) {
        await axios.put(`/api/v1/admin/chat_profiles/${data.user_id}`, submitData)
      } else {
        await axios.post('/api/v1/admin/chat_profiles', submitData)
      }
      setShowForm(false)
      setEditingProfile(null)
      setFormData({})
      loadChatProfiles()
    } catch (error) {
      alert('Failed to save chat profile: ' + (error.response?.data?.detail || error.message))
    }
  }

  const schema = [
    { name: 'user_id', label: 'User ID', required: true, placeholder: 'Уникальный идентификатор пользователя' },
    { name: 'full_name', label: 'Полное имя', required: true, placeholder: 'Иванов Иван Иванович' },
    { name: 'role', label: 'Должность', required: true, enum: [
      { value: 'user', label: 'Пользователь' },
      { value: 'admin', label: 'Администратор' },
      { value: 'moderator', label: 'Модератор' },
      { value: 'guest', label: 'Гость' },
      { value: 'engineer', label: 'Инженер' },
      { value: 'senior_engineer', label: 'Старший инженер' },
      { value: 'team_lead', label: 'Руководитель команды' },
      { value: 'director', label: 'Директор' },
      { value: 'hr_manager', label: 'Менеджер по персоналу' },
      { value: 'intern', label: 'Стажёр' },
      { value: 'employee', label: 'Сотрудник' }
    ] },
    { name: 'department', label: 'Отдел', required: true, enum: [
      { value: 'backend', label: 'Бэкенд' },
      { value: 'frontend', label: 'Фронтенд' },
      { value: 'engineering', label: 'Инженерия' },
      { value: 'hr', label: 'HR' },
      { value: 'sales', label: 'Продажи' },
      { value: 'marketing', label: 'Маркетинг' },
      { value: 'unknown', label: 'Неизвестно' }
    ] },
    { name: 'honorific_type', label: 'Вежливое обращение', required: true, enum: [
      { value: 'first_name', label: 'По имени' },
      { value: 'patronymic', label: 'По имени и отчеству' },
      { value: 'title', label: 'По должности' }
    ] },
    { name: 'communication_mode', label: 'Стиль общения', required: true, enum: [
      { value: 'informal', label: 'Неформальный' },
      { value: 'formal', label: 'Формальный' },
      { value: 'technical', label: 'Технический' },
      { value: 'collaborative', label: 'Коллаборативный' }
    ] },
    { name: 'core_user_id', label: 'Core User ID', required: false, placeholder: 'Ссылка на user_id из profiles' }
  ]

  const columns = [
    { key: 'user_id', label: 'User ID' },
    { key: 'full_name', label: 'Full Name' },
    { key: 'role', label: 'Role' },
    { key: 'department', label: 'Department' },
    { key: 'communication_mode', label: 'Mode' },
    { key: 'honorific_type', label: 'Honorific' },
    { key: 'core_user_id', label: 'Core User ID' }
  ]

  if (loading) {
    return <div className="loading">Loading chat profiles...</div>
  }

  return (
    <div className="chat-profiles-page">
      <div className="page-header">
        <h1>Chat Profiles</h1>
        <div className="header-actions">
          <button onClick={handleSyncAll} className="btn btn-primary">
            Sync to Core Engine
          </button>
          <button onClick={() => { setShowForm(true); setEditingProfile(null); setFormData({}); }} className="btn btn-primary">
            + Add Chat Profile
          </button>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={profiles}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onRefresh={loadChatProfiles}
      />

      {showForm && (
        <div className="modal">
          <div className="modal-content">
            <h2>{editingProfile ? 'Edit Chat Profile' : 'Create Chat Profile'}</h2>
            <form onSubmit={(e) => { e.preventDefault(); handleSubmit(formData) }}>
              {schema.map((field) => (
                <div key={field.name} className="form-group">
                  <label htmlFor={field.name}>{field.label}</label>
                  {field.enum ? (
                    <select
                      id={field.name}
                      value={formData[field.name] || ''}
                      onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
                    >
                      <option value="">Select...</option>
                      {field.enum.map((opt) => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      id={field.name}
                      type={field.type || 'text'}
                      value={formData[field.name] || ''}
                      onChange={(e) => setFormData({ ...formData, [field.name]: field.type === 'checkbox' ? e.target.checked : e.target.value })}
                      placeholder={field.placeholder}
                      required={field.required}
                    />
                  )}
                </div>
              ))}
              <div className="form-actions">
                <button type="button" onClick={() => setShowForm(false)} className="btn btn-secondary">Cancel</button>
                <button type="submit" className="btn btn-primary">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default ChatProfiles
