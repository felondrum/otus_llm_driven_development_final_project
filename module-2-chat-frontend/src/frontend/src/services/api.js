// ===========================================
// API Service for Chat Frontend
// ===========================================

const API_BASE_URL = '/api/v1'

export const apiService = {
  async getUsers() {
    try {
      const response = await fetch(`${API_BASE_URL}/users`)
      if (!response.ok) {
        throw new Error('Failed to fetch users')
      }
      const data = await response.json()
      return data.users
    } catch (error) {
      console.error('Error fetching users:', error)
      throw error
    }
  },

  async getStyles() {
    try {
      const response = await fetch(`${API_BASE_URL}/styles`)
      if (!response.ok) {
        throw new Error('Failed to fetch styles')
      }
      const data = await response.json()
      return data.styles
    } catch (error) {
      console.error('Error fetching styles:', error)
      throw error
    }
  },

  async getHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`)
      if (!response.ok) {
        throw new Error('Health check failed')
      }
      return await response.json()
    } catch (error) {
      console.error('Health check error:', error)
      throw error
    }
  }
}
