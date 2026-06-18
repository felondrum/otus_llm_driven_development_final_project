// ===========================================
// Login Component - User Selection
// ===========================================

import React, { useState, useEffect } from 'react'
import { apiService } from '../services/api'

function Login({ onLogin, users }) {
  const [selectedUser, setSelectedUser] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Load users from API
    const loadUsers = async () => {
      try {
        const users = await apiService.getUsers()
        if (users && users.length > 0) {
          setSelectedUser(users[0].user_id)
        }
        setIsLoading(false)
      } catch (error) {
        console.error('Error loading users:', error)
        setIsLoading(false)
      }
    }

    loadUsers()
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (selectedUser) {
      onLogin(selectedUser)
    }
  }

  if (isLoading) {
    return (
      <div className="login-container">
        <p>Загрузка пользователей...</p>
      </div>
    )
  }

  return (
    <div className="login-container">
      <h1>Chameleon Chat</h1>
      <p>Выберите пользователя для входа</p>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="user-select">Ваше имя:</label>
          <select
            id="user-select"
            value={selectedUser}
            onChange={(e) => setSelectedUser(e.target.value)}
            required
          >
            {users?.map((user) => (
              <option key={user.user_id} value={user.user_id}>
                {user.full_name} ({user.user_id})
              </option>
            ))}
          </select>
        </div>
        
        <button type="submit" className="btn-primary">
          Войти в чат
        </button>
      </form>
    </div>
  )
}

export default Login
