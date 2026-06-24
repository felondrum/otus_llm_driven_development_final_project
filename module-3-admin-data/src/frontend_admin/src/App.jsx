import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Profiles from './pages/Profiles'
import Rules from './pages/Rules'
import Styles from './pages/Styles'
import Documents from './pages/Documents'
import System from './pages/System'
import ChatProfiles from './pages/ChatProfiles'
import Qdrant from './pages/Qdrant'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/profiles" element={<Profiles />} />
        <Route path="/chat_profiles" element={<ChatProfiles />} />
        <Route path="/rules" element={<Rules />} />
        <Route path="/styles" element={<Styles />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/system" element={<System />} />
        <Route path="/qdrant" element={<Qdrant />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
