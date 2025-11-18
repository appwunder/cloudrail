import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { awsAccountsApi } from '@/lib/api'
import { Cloud, Plus, RefreshCw, Trash2, X, AlertCircle, CheckCircle, Loader } from 'lucide-react'

interface AWSAccount {
  id: string
  account_id: string
  account_name: string
  role_arn: string
  external_id?: string
  region: string
  sync_status: 'pending' | 'syncing' | 'success' | 'error'
  last_sync_at?: string
  created_at: string
}

export default function AWSAccounts() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [formData, setFormData] = useState({
    account_id: '',
    account_name: '',
    role_arn: '',
    external_id: '',
    region: 'us-east-1',
  })
  const [error, setError] = useState('')
  const queryClient = useQueryClient()

  // Fetch AWS accounts
  const { data: accounts, isLoading } = useQuery<AWSAccount[]>({
    queryKey: ['aws-accounts'],
    queryFn: async () => {
      const response = await awsAccountsApi.list()
      return response.data
    },
  })

  // Create AWS account mutation
  const createAccountMutation = useMutation({
    mutationFn: (data: typeof formData) => awsAccountsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aws-accounts'] })
      setIsModalOpen(false)
      setFormData({
        account_id: '',
        account_name: '',
        role_arn: '',
        external_id: '',
        region: 'us-east-1',
      })
      setError('')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to link AWS account')
    },
  })

  // Sync account mutation
  const syncAccountMutation = useMutation({
    mutationFn: (accountId: string) => awsAccountsApi.sync(accountId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aws-accounts'] })
    },
  })

  // Delete account mutation
  const deleteAccountMutation = useMutation({
    mutationFn: (accountId: string) => awsAccountsApi.delete(accountId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aws-accounts'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    createAccountMutation.mutate(formData)
  }

  const handleSync = (accountId: string) => {
    syncAccountMutation.mutate(accountId)
  }

  const handleDelete = (accountId: string) => {
    if (window.confirm('Are you sure you want to remove this AWS account?')) {
      deleteAccountMutation.mutate(accountId)
    }
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      pending: 'bg-gray-100 text-gray-800',
      syncing: 'bg-blue-100 text-blue-800',
      success: 'bg-green-100 text-green-800',
      error: 'bg-red-100 text-red-800',
    }
    const icons = {
      pending: Loader,
      syncing: RefreshCw,
      success: CheckCircle,
      error: AlertCircle,
    }
    const Icon = icons[status as keyof typeof icons]
    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status as keyof typeof styles]}`}>
        <Icon className={`h-3.5 w-3.5 ${status === 'syncing' ? 'animate-spin' : ''}`} />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AWS Accounts</h1>
          <p className="text-sm text-gray-600 mt-1">Manage your linked AWS accounts</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Link AWS Account
        </button>
      </div>

      {isLoading ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="text-center text-gray-500">
            <Loader className="h-8 w-8 mx-auto mb-4 animate-spin" />
            <p>Loading AWS accounts...</p>
          </div>
        </div>
      ) : accounts && accounts.length > 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Account
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Account ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Region
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Sync
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {accounts.map((account) => (
                <tr key={account.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-primary-100 rounded-lg">
                        <Cloud className="h-5 w-5 text-primary-600" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">{account.account_name}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {account.account_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {account.region}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(account.sync_status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {account.last_sync_at
                      ? new Date(account.last_sync_at).toLocaleDateString()
                      : 'Never'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => handleSync(account.id)}
                        disabled={syncAccountMutation.isPending}
                        className="text-primary-600 hover:text-primary-900 disabled:opacity-50"
                        title="Sync costs"
                      >
                        <RefreshCw className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(account.id)}
                        disabled={deleteAccountMutation.isPending}
                        className="text-red-600 hover:text-red-900 disabled:opacity-50"
                        title="Remove account"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
              <Cloud className="h-8 w-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No AWS accounts linked yet</h3>
            <p className="text-sm text-gray-500 mb-6">
              Link your first AWS account to start analyzing costs
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Plus className="h-4 w-4" />
              Link AWS Account
            </button>
          </div>
        </div>
      )}

      {/* Add AWS Account Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Link AWS Account</h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {error && (
                <div className="rounded-lg bg-red-50 p-4 flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <div>
                <label htmlFor="account_name" className="block text-sm font-medium text-gray-700 mb-1">
                  Account Name *
                </label>
                <input
                  id="account_name"
                  type="text"
                  required
                  value={formData.account_name}
                  onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Production AWS Account"
                />
                <p className="mt-1 text-xs text-gray-500">A friendly name for this AWS account</p>
              </div>

              <div>
                <label htmlFor="account_id" className="block text-sm font-medium text-gray-700 mb-1">
                  AWS Account ID *
                </label>
                <input
                  id="account_id"
                  type="text"
                  required
                  value={formData.account_id}
                  onChange={(e) => setFormData({ ...formData, account_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="123456789012"
                />
                <p className="mt-1 text-xs text-gray-500">Your 12-digit AWS account ID</p>
              </div>

              <div>
                <label htmlFor="role_arn" className="block text-sm font-medium text-gray-700 mb-1">
                  IAM Role ARN *
                </label>
                <input
                  id="role_arn"
                  type="text"
                  required
                  value={formData.role_arn}
                  onChange={(e) => setFormData({ ...formData, role_arn: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="arn:aws:iam::123456789012:role/CloudRailRole"
                />
                <p className="mt-1 text-xs text-gray-500">
                  The ARN of the IAM role with cost explorer access
                </p>
              </div>

              <div>
                <label htmlFor="external_id" className="block text-sm font-medium text-gray-700 mb-1">
                  External ID
                </label>
                <input
                  id="external_id"
                  type="text"
                  value={formData.external_id}
                  onChange={(e) => setFormData({ ...formData, external_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="unique-external-id"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Optional external ID for additional security
                </p>
              </div>

              <div>
                <label htmlFor="region" className="block text-sm font-medium text-gray-700 mb-1">
                  Default Region *
                </label>
                <select
                  id="region"
                  required
                  value={formData.region}
                  onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="us-east-1">US East (N. Virginia)</option>
                  <option value="us-east-2">US East (Ohio)</option>
                  <option value="us-west-1">US West (N. California)</option>
                  <option value="us-west-2">US West (Oregon)</option>
                  <option value="eu-west-1">EU (Ireland)</option>
                  <option value="eu-central-1">EU (Frankfurt)</option>
                  <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
                  <option value="ap-northeast-1">Asia Pacific (Tokyo)</option>
                </select>
                <p className="mt-1 text-xs text-gray-500">Primary AWS region for this account</p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createAccountMutation.isPending}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createAccountMutation.isPending ? 'Linking...' : 'Link Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
