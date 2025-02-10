import './App.css'
import { BrowserRouter, Route, Routes } from 'react-router'
import Login from './views/Login'

function App() {
  return (
    <BrowserRouter>
    <Routes>
      <Route path="/" element={<h1>Home</h1>} />
      <Route path="/login" element={<Login />} />
    </Routes>
    </BrowserRouter>
  )
}

export default App
