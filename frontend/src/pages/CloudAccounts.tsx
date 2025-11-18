import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Cloud, Trash2, RefreshCw, CheckCircle, XCircle, Clock } from 'lucide-react'
import { api } from '@/lib/api'

// Cloud Provider types
type CloudProvider = 'aws' | 'gcp' | 'azure' | 'alibaba'

interface CloudAccount {
  id: string
  tenant_id: string
  provider: CloudProvider
  account_id: string
  account_name: string | null
  region: string | null
  currency: string
  is_active: boolean
  last_sync_at: string | null
  sync_status: string
  sync_error: string | null
  created_at: string
}

interface CloudAccountsResponse {
  accounts: CloudAccount[]
  total: number
}

// Provider configurations
const PROVIDERS = {
  aws: {
    name: 'Amazon Web Services',
    color: '#FF9900',
    icon: '☁️',
    credentialFields: [
      { name: 'role_arn', label: 'IAM Role ARN', type: 'text', required: true, placeholder: 'arn:aws:iam::123456789012:role/CloudRailRole' },
      { name: 'external_id', label: 'External ID (Optional)', type: 'text', required: false }
    ]
  },
  gcp: {
    name: 'Google Cloud Platform',
    color: '#4285F4',
    icon: '🔵',
    credentialFields: [
      { name: 'service_account_json', label: 'Service Account JSON', type: 'textarea', required: true, placeholder: '{ "type": "service_account", ... }' }
    ]
  },
  azure: {
    name: 'Microsoft Azure',
    color: '#0078D4',
    icon: '🔷',
    credentialFields: [
      { name: 'tenant_id', label: 'Tenant ID', type: 'text', required: true },
      { name: 'client_id', label: 'Client ID', type: 'text', required: true },
      { name: 'client_secret', label: 'Client Secret', type: 'password', required: true }
    ]
  },
  alibaba: {
    name: 'Alibaba Cloud',
    color: '#FF6A00',
    icon: '🟠',
    credentialFields: [
      { name: 'access_key_id', label: 'Access Key ID', type: 'text', required: true },
      { name: 'access_key_secret', label: 'Access Key Secret', type: 'password', required: true }
    ]
  }
}

export default function CloudAccounts() {
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState<CloudProvider>('aws')
  const [formData, setFormData] = useState({
    account_id: '',
    account_name: '',
    region: '',
    currency: 'USD',
    credentials: {} as Record<string, any>
  })

  // Fetch cloud accounts
  const { data: accountsData, isLoading } = useQuery<CloudAccountsResponse>({
    queryKey: ['cloud-accounts'],
    queryFn: async () => {
      const response = await api.get('/api/v1/cloud-accounts/')
      return response.data
    }
  })

  // Create account mutation
  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/api/v1/cloud-accounts/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cloud-accounts'] })
      setIsModalOpen(false)
      resetForm()
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to create cloud account')
    }
  })

  // Delete account mutation
  const deleteMutation = useMutation({
    mutationFn: async (accountId: string) => {
      await api.delete(`/api/v1/cloud-accounts/${accountId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cloud-accounts'] })
    }
  })

  // Sync account mutation
  const syncMutation = useMutation({
    mutationFn: async (accountId: string) => {
      const response = await api.post(`/api/v1/cloud-accounts/${accountId}/sync`, { force: false })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cloud-accounts'] })
    }
  })

  const resetForm = () => {
    setFormData({
      account_id: '',
      account_name: '',
      region: '',
      currency: 'USD',
      credentials: {}
    })
    setSelectedProvider('aws')
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const payload = {
      provider: selectedProvider,
      account_id: formData.account_id,
      account_name: formData.account_name || null,
      region: formData.region || null,
      currency: formData.currency,
      credentials: formData.credentials,
      config_data: null
    }

    createMutation.mutate(payload)
  }

  const getSyncStatusBadge = (status: string) => {
    const badges = {
      pending: { icon: Clock, color: 'bg-gray-100 text-gray-700', text: 'Pending' },
      syncing: { icon: RefreshCw, color: 'bg-blue-100 text-blue-700', text: 'Syncing' },
      success: { icon: CheckCircle, color: 'bg-green-100 text-green-700', text: 'Success' },
      error: { icon: XCircle, color: 'bg-red-100 text-red-700', text: 'Error' }
    }

    const badge = badges[status as keyof typeof badges] || badges.pending
    const Icon = badge.icon

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${badge.color}`}>
        <Icon className="w-3 h-3" />
        {badge.text}
      </span>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cloud Accounts</h1>
          <p className="text-gray-600 mt-1">Manage your multi-cloud accounts</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Link Cloud Account
        </button>
      </div>

      {/* Accounts Grid */}
      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Loading accounts...</div>
        </div>
      ) : accountsData && accountsData.accounts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {accountsData.accounts.map((account) => {
            const provider = PROVIDERS[account.provider]
            return (
              <div
                key={account.id}
                className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{provider.icon}</span>
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {account.account_name || account.account_id}
                      </h3>
                      <p className="text-xs text-gray-500">{provider.name}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => deleteMutation.mutate(account.id)}
                    className="text-red-600 hover:text-red-800 p-1"
                    title="Delete account"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-500">Account ID:</span>
                    <span className="ml-2 font-mono text-gray-900">{account.account_id}</span>
                  </div>

                  {account.region && (
                    <div>
                      <span className="text-gray-500">Region:</span>
                      <span className="ml-2 text-gray-900">{account.region}</span>
                    </div>
                  )}

                  <div>
                    <span className="text-gray-500">Currency:</span>
                    <span className="ml-2 text-gray-900">{account.currency}</span>
                  </div>

                  <div>
                    <span className="text-gray-500">Status:</span>
                    <span className="ml-2">{getSyncStatusBadge(account.sync_status)}</span>
                  </div>

                  {account.last_sync_at && (
                    <div>
                      <span className="text-gray-500">Last Sync:</span>
                      <span className="ml-2 text-gray-900">
                        {new Date(account.last_sync_at).toLocaleString()}
                      </span>
                    </div>
                  )}
                </div>

                <button
                  onClick={() => syncMutation.mutate(account.id)}
                  disabled={syncMutation.isPending}
                  className="mt-4 w-full px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <RefreshCw className={`w-4 h-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
                  Sync Data
                </button>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <Cloud className="w-12 h-12 text-gray-400 mb-3" />
          <p className="text-gray-600 font-medium">No cloud accounts linked</p>
          <p className="text-gray-500 text-sm mt-1">Click "Link Cloud Account" to get started</p>
        </div>
      )}

      {/* Add Account Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">Link Cloud Account</h2>
                <button
                  onClick={() => {
                    setIsModalOpen(false)
                    resetForm()
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Provider Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cloud Provider
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    {(Object.keys(PROVIDERS) as CloudProvider[]).map((provider) => (
                      <button
                        key={provider}
                        type="button"
                        onClick={() => {
                          setSelectedProvider(provider)
                          setFormData({ ...formData, credentials: {} })
                        }}
                        className={`p-4 border-2 rounded-lg text-left transition-all ${
                          selectedProvider === provider
                            ? 'border-primary-500 bg-primary-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{PROVIDERS[provider].icon}</span>
                          <span className="font-medium text-gray-900">{PROVIDERS[provider].name}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Account Details */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Account ID *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.account_id}
                      onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder={selectedProvider === 'aws' ? '123456789012' : ''}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Account Name
                    </label>
                    <input
                      type="text"
                      value={formData.account_name}
                      onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="Production Account"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Default Region
                    </label>
                    <input
                      type="text"
                      value={formData.region}
                      onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="us-east-1"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Currency
                    </label>
                    <select
                      value={formData.currency}
                      onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="USD">USD</option>
                      <option value="EUR">EUR</option>
                      <option value="GBP">GBP</option>
                      <option value="CNY">CNY</option>
                    </select>
                  </div>
                </div>

                {/* Credentials */}
                <div className="border-t pt-4">
                  <h3 className="text-sm font-medium text-gray-900 mb-3">Credentials</h3>
                  <div className="space-y-4">
                    {PROVIDERS[selectedProvider].credentialFields.map((field) => (
                      <div key={field.name}>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          {field.label} {field.required && '*'}
                        </label>
                        {field.type === 'textarea' ? (
                          <textarea
                            required={field.required}
                            value={formData.credentials[field.name] || ''}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                credentials: { ...formData.credentials, [field.name]: e.target.value }
                              })
                            }
                            rows={4}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-xs"
                            placeholder={field.placeholder}
                          />
                        ) : (
                          <input
                            type={field.type}
                            required={field.required}
                            value={formData.credentials[field.name] || ''}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                credentials: { ...formData.credentials, [field.name]: e.target.value }
                              })
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                            placeholder={field.placeholder}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Submit Buttons */}
                <div className="flex gap-3 justify-end border-t pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setIsModalOpen(false)
                      resetForm()
                    }}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createMutation.isPending}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                  >
                    {createMutation.isPending ? 'Linking...' : 'Link Account'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
