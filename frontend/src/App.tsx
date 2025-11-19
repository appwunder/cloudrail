import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Register from './pages/Register'
import AWSAccounts from './pages/AWSAccounts'
import CloudAccounts from './pages/CloudAccounts'
import CostExplorer from './pages/CostExplorer'
import Recommendations from './pages/Recommendations'
import ArchitectureDesigner from './pages/ArchitectureDesigner'
import Budgets from './pages/Budgets'
import Pricing from './pages/Pricing'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/aws-accounts" element={<AWSAccounts />} />
          <Route path="/cloud-accounts" element={<CloudAccounts />} />
          <Route path="/cost-explorer" element={<CostExplorer />} />
          <Route path="/recommendations" element={<Recommendations />} />
          <Route path="/budgets" element={<Budgets />} />
          <Route path="/architecture-designer" element={<ArchitectureDesigner />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
