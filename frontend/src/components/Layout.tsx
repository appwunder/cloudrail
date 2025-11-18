import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Cloud, CloudCog, TrendingDown, Lightbulb, DollarSign, Boxes, LogOut } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useEffect } from 'react'
import CloudRailLogo from './CloudRailLogo'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'AWS Accounts', href: '/aws-accounts', icon: Cloud },
  { name: 'Cloud Accounts', href: '/cloud-accounts', icon: CloudCog },
  { name: 'Cost Explorer', href: '/cost-explorer', icon: TrendingDown },
  { name: 'Recommendations', href: '/recommendations', icon: Lightbulb },
  { name: 'Budgets', href: '/budgets', icon: DollarSign },
  { name: 'Architecture Designer', href: '/architecture-designer', icon: Boxes },
]

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, fetchUser, logout, isAuthenticated } = useAuthStore()

  useEffect(() => {
    if (isAuthenticated && !user) {
      fetchUser().catch(() => {
        navigate('/login')
      })
    } else if (!isAuthenticated) {
      navigate('/login')
    }
  }, [isAuthenticated, user, fetchUser, navigate])

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const getUserInitial = () => {
    if (user?.full_name) {
      return user.full_name.charAt(0).toUpperCase()
    }
    if (user?.email) {
      return user.email.charAt(0).toUpperCase()
    }
    return 'U'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 h-16 px-6 border-b border-gray-200">
            <CloudRailLogo size={32} className="text-primary-600" />
            <h1 className="text-xl font-bold text-primary-600">CloudRail</h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.name}
                </Link>
              )
            })}
          </nav>

          {/* User section */}
          <div className="p-4 border-t border-gray-200 space-y-2">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                <span className="text-sm font-medium text-primary-700">{getUserInitial()}</span>
              </div>
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700 truncate">
                  {user?.full_name || 'User'}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {user?.email || 'user@example.com'}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="pl-64">
        <main className="py-6">
          <div className="px-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
