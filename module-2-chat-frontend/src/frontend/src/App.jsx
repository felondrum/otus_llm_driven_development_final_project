// ===========================================
// Main App Component
// ===========================================

import React, { useState, useEffect } from 'react'
import Login from './components/Login'
import ChatRoom from './components/ChatRoom'

function App() {
  const [user_id, setUser_id] = useState(null)
  const [users, setUsers] = useState([])
  const [isLoading, setIsLoading] = useState(true)

  // Load users from API on mount
  useEffect(() => {
    const loadUsers = async () => {
      try {
        const response = await fetch('/api/v1/users')
        if (response.ok) {
          const data = await response.json()
          setUsers(data.users || [])
        }
      } catch (error) {
        console.error('Error loading users:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadUsers()
  }, [])

  const handleLogin = (userId) => {
    setUser_id(userId)
  }

  const handleLogout = () => {
    setUser_id(null)
  }

  if (isLoading) {
    return (
      <div className="app">
        <div className="login-container">
          <p>Загрузка...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      {user_id ? (
        <ChatRoom user_id={user_id} onLogout={handleLogout} />
      ) : (
        <Login onLogin={handleLogin} users={users} />
      )}
    </div>
  )
}

export default App
