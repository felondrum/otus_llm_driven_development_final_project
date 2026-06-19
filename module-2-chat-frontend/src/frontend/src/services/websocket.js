// ===========================================
// WebSocket Service for Chat Frontend
// ===========================================

class WebSocketService {
  constructor() {
    this.ws = null
    this.onMessage = null
    this.onConnect = null
    this.onDisconnect = null
    this.onAuth = null
    this.onMessageReceived = null
  }

  connect(url, onConnect, onDisconnect) {
    this.ws = new WebSocket(url)
    
    this.ws.onopen = () => {
      console.log('WebSocket connected')
      // Use provided callback or instance property
      if (onConnect) onConnect()
      else if (this.onConnect) this.onConnect()
    }
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      // Use provided callback or instance property
      if (onDisconnect) onDisconnect()
      else if (this.onDisconnect) this.onDisconnect()
    }
    
    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        this.handleMessage(message)
      } catch (error) {
        console.error('Error parsing message:', error)
      }
    }
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  handleMessage(message) {
    const type = message.type
    
    switch (type) {
      case 'welcome':
        console.log('Welcome message:', message)
        if (this.onMessage) this.onMessage(message)
        break
      
      case 'auth_ok':
        console.log('Auth OK:', message)
        if (this.onAuth) this.onAuth(message)
        break
      
      case 'error':
        console.error('Error:', message)
        if (this.onMessage) this.onMessage(message)
        break
      
      case 'message':
        console.log('Message received:', message)
        if (this.onMessageReceived) this.onMessageReceived(message)
        break
      
      case 'recipient_selected':
        console.log('Recipient selected:', message)
        if (this.onMessage) this.onMessage(message)
        break
      
      default:
        console.log('Unknown message type:', type)
        if (this.onMessage) this.onMessage(message)
    }
  }

  // Client actions
  auth(userId) {
    this.send({ type: 'auth', user_id: userId })
  }

  selectRecipient(recipientId) {
    this.send({ type: 'select_recipient', recipient_id: recipientId })
  }

  sendMessage(text, style = '') {
    this.send({ 
      type: 'message', 
      text, 
      style,
      timestamp: new Date().toISOString()
    })
  }
}

export const websocketService = new WebSocketService()
