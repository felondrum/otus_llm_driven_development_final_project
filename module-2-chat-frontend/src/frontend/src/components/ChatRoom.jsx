// ===========================================
// Chat Room Component
// ===========================================

import React, { useState, useEffect, useRef } from 'react'
import { apiService } from '../services/api'
import { websocketService } from '../services/websocket'

function ChatRoom({ user_id, onLogout }) {
  const [users, setUsers] = useState([])
  const [styles, setStyles] = useState([])
  const [messages, setMessages] = useState({}) // Хранилище сообщений по получателям: {recipient_id: [message1, message2, ...]}
  const [selectedRecipient, setSelectedRecipient] = useState('')
  const [selectedStyle, setSelectedStyle] = useState('')
  const [inputText, setInputText] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [showOriginal, setShowOriginal] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  
  const messagesEndRef = useRef(null)
  const wsUrl = useRef(null)
  const loadedRecipients = useRef(new Set()) // Отслеживание загруженных историй

  // Set random background on mount
  useEffect(() => {
    const randomColor = `hsl(${Math.random() * 360}, 70%, 85%)`
    document.body.style.background = randomColor
    
    // Load users and styles
    loadUsersAndStyles()
    
    // Setup WebSocket
    setupWebSocket()
    
    return () => {
      websocketService.disconnect()
    }
  }, [])

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, selectedRecipient])

  const loadUsersAndStyles = async () => {
    try {
      const [users, styles] = await Promise.all([
        apiService.getUsers(),
        apiService.getStyles()
      ])
      setUsers(users)
      setStyles(styles)
      
      // Select first user as default recipient (not self)
      if (users.length > 0) {
        const otherUsers = users.filter(u => u.user_id !== user_id)
        if (otherUsers.length > 0) {
          setSelectedRecipient(otherUsers[0].user_id)
        }
      }
    } catch (error) {
      console.error('Error loading data:', error)
    }
  }

  const setupWebSocket = () => {
    // Use absolute URL with current origin and /ws path
    // This ensures WebSocket connects to the same host and port as the page
    wsUrl.current = `${window.location.origin}/ws`
    
    // Log connection info for debugging
    console.log('WebSocket connecting to:', wsUrl.current)
    
    websocketService.onConnect = () => {
      console.log('WebSocket onConnect called')
      setIsConnected(true)
      websocketService.auth(user_id)
    }
    
    websocketService.onDisconnect = () => {
      console.log('WebSocket onDisconnect called')
      setIsConnected(false)
    }
    
    websocketService.onAuth = (message) => {
      console.log('Authenticated:', message)
    }
    
    websocketService.onMessageReceived = (message) => {
      console.log('Message received:', message)
      
      // Добавляем сообщение в историю конкретного получателя
      const senderId = message.from
      const recipientId = message.to
      
      // Определяем, с кем ведется диалог
      // Если это сообщение, которое я отправил - получатель是我的 собеседник
      // Если это сообщение, которое я получил - отправитель是我的 собеседник
      // Если это сообщение, которое я отправил сам себе (тестовый кейс) - получатель是我的 собеседник
      let chatPartner
      if (senderId === user_id) {
        chatPartner = recipientId
      } else {
        chatPartner = senderId
      }
      
      setMessages(prev => ({
        ...prev,
        [chatPartner]: [...(prev[chatPartner] || []), message]
      }))
    }
    
    websocketService.onMessage = (message) => {
      console.log('WS message:', message)
      
      // Handle welcome message
      if (message.type === 'welcome' && !selectedRecipient && message.available_users) {
        const otherUsers = message.available_users.filter(u => u.user_id !== user_id)
        if (otherUsers.length > 0) {
          const firstRecipient = otherUsers[0].user_id
          setSelectedRecipient(firstRecipient)
          websocketService.selectRecipient(firstRecipient)
          // Загружаем историю при первом открытии
          loadChatHistory(firstRecipient)
        }
      }
    }
    
    websocketService.connect(wsUrl.current)
  }

  const handleSendMessage = (e) => {
    e.preventDefault()
    
    if (!inputText.trim() || !selectedRecipient) {
      return
    }
    
    websocketService.sendMessage(inputText, selectedStyle)
    setInputText('')
  }

  const handleRecipientChange = (recipientId) => {
    console.log('handleRecipientChange called with:', recipientId)
    setSelectedRecipient(recipientId)
    
    // Загружаем историю для нового получателя
    loadChatHistory(recipientId)
    
    websocketService.selectRecipient(recipientId)
  }

  // Load chat history from backend
  const loadChatHistory = async (recipientId) => {
    console.log('loadChatHistory called with:', recipientId)
    if (loadedRecipients.current.has(recipientId)) {
      console.log('History already loaded for recipient:', recipientId)
      return
    }
    
    setIsLoadingHistory(true)
    try {
      console.log('Fetching history from /api/v1/messages/' + recipientId)
      const response = await fetch(`/api/v1/messages/${recipientId}`)
      console.log('History response:', response.status)
      if (response.ok) {
        const data = await response.json()
        const historyMessages = data.messages || []
        
        // Фильтруем только сообщения, которые относятся к текущему пользователю
        // (отправленные нами или полученные нами)
        const filteredMessages = historyMessages.filter(msg => 
          msg.from === user_id || msg.to === user_id
        )
        
        setMessages(prev => ({
          ...prev,
          [recipientId]: filteredMessages
        }))
        
        loadedRecipients.current.add(recipientId)
        console.log('Loaded history for', recipientId, ':', filteredMessages.length, 'messages (filtered from', historyMessages.length, ')')
      }
    } catch (error) {
      console.error('Error loading chat history:', error)
    } finally {
      setIsLoadingHistory(false)
    }
  }

  const getUserFullName = (userId) => {
    const user = users.find(u => u.user_id === userId)
    return user ? user.full_name : userId
  }

  const getRecipientName = () => {
    return getUserFullName(selectedRecipient)
  }

  return (
    <div className="chat-room">
      <header className="chat-header">
        <h2>Chameleon Chat</h2>
        <p className="user-info">
          Вы: {getUserFullName(user_id)} | 
          Собеседник: {getRecipientName()}
        </p>
        <p className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '● Подключено' : '○ Отключено'}
        </p>
      </header>

      <div className="chat-container">
        {/* User list */}
        <div className="user-list">
          <h3>Пользователи</h3>
          <ul>
            {users.filter(u => u.user_id !== user_id).map(user => (
              <li 
                key={user.user_id}
                className={user.user_id === selectedRecipient ? 'selected' : ''}
                onClick={() => handleRecipientChange(user.user_id)}
              >
                {user.full_name}
              </li>
            ))}
          </ul>
        </div>

        {/* Message list */}
        <div className="message-list">
          {isLoadingHistory ? (
            <div className="loading-messages">Загрузка истории...</div>
          ) : (
            (messages[selectedRecipient] || []).map((msg, index) => (
              <div key={msg.id || index} className={`message ${msg.from === user_id ? 'sent' : 'received'}`}>
                <div className="message-content">
                  {msg.adapted_text && showOriginal ? (
                    <>
                      <div className="adapted-message">
                        {msg.adapted_text}
                        {msg.style && <span className="style-badge">{msg.style}</span>}
                      </div>
                      <div className="original-message">
                        {msg.text}
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="message-text">
                        {msg.adapted_text || msg.text}
                      </div>
                      {msg.style && (
                        <div className="style-info">
                          <span className="style-badge">{msg.style}</span>
                          {msg.was_adapted && <span className="adapted-badge">Адаптировано</span>}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="input-area">
          <div className="input-controls">
            <select 
              value={selectedStyle}
              onChange={(e) => setSelectedStyle(e.target.value)}
              placeholder="Выберите стиль"
            >
              <option value="">Без стиля</option>
              {styles.map(style => (
                <option key={style.id} value={style.id}>
                  {style.name}
                </option>
              ))}
            </select>
            
            <label>
              <input 
                type="checkbox" 
                checked={showOriginal}
                onChange={(e) => setShowOriginal(e.target.checked)}
              />
              Показать оригинал
            </label>
          </div>

          <form onSubmit={handleSendMessage} className="message-form">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Введите сообщение..."
              disabled={!isConnected}
            />
            <button type="submit" disabled={!isConnected || !inputText.trim()}>
              Отправить
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default ChatRoom
