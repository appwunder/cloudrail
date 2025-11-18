import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { costsApi, awsAccountsApi } from '@/lib/api'

interface Recommendation {
  id: string
  type: string
  category: string
  severity: 'low' | 'medium' | 'high'
  title: string
  description: string
  resource?: string
  current_config?: string
  recommended_config?: string
  potential_savings: number
  savings_currency: string
  action?: string
  effort?: string
}

export default function Recommendations() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all')

  // Fetch AWS accounts
  const { data: accountsData } = useQuery({
    queryKey: ['awsAccounts'],
    queryFn: async () => {
      const response = await awsAccountsApi.list()
      return response.data
    },
    retry: 1
  })

  const firstAccountId = accountsData?.length > 0 ? accountsData[0].id : null

  // Fetch recommendations
  const { data: recommendationsData, isLoading } = useQuery({
    queryKey: ['recommendations', firstAccountId],
    queryFn: async () => {
      const response = await costsApi.getRecommendations(firstAccountId)
      return response.data
    },
    enabled: !!firstAccountId,
    retry: 1
  })

  const recommendations: Recommendation[] = recommendationsData?.recommendations || []
  const totalSavings = recommendationsData?.total_potential_savings || 0

  // Filter recommendations
  const filteredRecommendations = recommendations.filter(rec => {
    if (selectedCategory !== 'all' && rec.category !== selectedCategory) return false
    if (selectedSeverity !== 'all' && rec.severity !== selectedSeverity) return false
    return true
  })

  // Group by category
  const categories = ['all', ...new Set(recommendations.map(r => r.category))]
  const severities = ['all', 'high', 'medium', 'low']

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'compute': return '🖥️'
      case 'storage': return '💾'
      case 'database': return '🗄️'
      case 'commitment': return '💰'
      case 'general': return '📊'
      default: return '💡'
    }
  }

  if (!firstAccountId) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Cost Optimization Recommendations</h1>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="text-center text-gray-500">
            <p className="mb-4">No AWS accounts connected</p>
            <p className="text-sm">Link your AWS account to receive personalized cost optimization recommendations</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Cost Optimization Recommendations</h1>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Total Recommendations</h3>
          <p className="text-3xl font-bold text-gray-900">{recommendations.length}</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Potential Monthly Savings</h3>
          <p className="text-3xl font-bold text-green-600">${totalSavings.toFixed(2)}</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">High Priority Items</h3>
          <p className="text-3xl font-bold text-red-600">
            {recommendations.filter(r => r.severity === 'high').length}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Category:</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Severity:</label>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              {severities.map(sev => (
                <option key={sev} value={sev}>
                  {sev.charAt(0).toUpperCase() + sev.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div className="ml-auto text-sm text-gray-600">
            Showing {filteredRecommendations.length} of {recommendations.length} recommendations
          </div>
        </div>
      </div>

      {/* Recommendations List */}
      {isLoading ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="text-center text-gray-500">Loading recommendations...</div>
        </div>
      ) : filteredRecommendations.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="text-center text-gray-500">
            <p className="mb-4">No recommendations found</p>
            <p className="text-sm">Your infrastructure is well-optimized or filters are too restrictive</p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredRecommendations.map((rec) => (
            <div
              key={rec.id}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{getCategoryIcon(rec.category)}</span>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">{rec.title}</h3>
                    <p className="text-sm text-gray-600">{rec.description}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <span className={`px-3 py-1 text-xs font-medium rounded-full border ${getSeverityColor(rec.severity)}`}>
                    {rec.severity.toUpperCase()}
                  </span>
                  {rec.effort && (
                    <span className="px-3 py-1 text-xs font-medium rounded-full border bg-gray-100 text-gray-700 border-gray-200">
                      {rec.effort.toUpperCase()} EFFORT
                    </span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                {rec.current_config && (
                  <div>
                    <span className="text-xs font-medium text-gray-500">Current:</span>
                    <p className="text-sm text-gray-900 mt-1">{rec.current_config}</p>
                  </div>
                )}
                {rec.recommended_config && (
                  <div>
                    <span className="text-xs font-medium text-gray-500">Recommended:</span>
                    <p className="text-sm text-green-700 font-medium mt-1">{rec.recommended_config}</p>
                  </div>
                )}
              </div>

              {rec.action && (
                <div className="mb-4">
                  <span className="text-xs font-medium text-gray-500">Action:</span>
                  <p className="text-sm text-gray-900 mt-1">{rec.action}</p>
                </div>
              )}

              {rec.resource && (
                <div className="mb-4">
                  <span className="text-xs font-medium text-gray-500">Resource:</span>
                  <p className="text-sm text-gray-700 font-mono mt-1">{rec.resource}</p>
                </div>
              )}

              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">Potential Savings:</span>
                  <span className="text-lg font-bold text-green-600">
                    ${rec.potential_savings.toFixed(2)}/month
                  </span>
                </div>
                <span className="text-xs text-gray-500 uppercase">{rec.category}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary Footer */}
      {filteredRecommendations.length > 0 && (
        <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-green-900 mb-1">
                Total Estimated Savings
              </h3>
              <p className="text-sm text-green-700">
                By implementing {filteredRecommendations.length} recommendation(s)
              </p>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold text-green-600">
                ${filteredRecommendations.reduce((sum, rec) => sum + rec.potential_savings, 0).toFixed(2)}
              </p>
              <p className="text-sm text-green-700">per month</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
