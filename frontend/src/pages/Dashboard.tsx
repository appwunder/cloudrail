import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { costsApi } from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { AlertTriangle, DollarSign, TrendingUp } from 'lucide-react'
import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

const API_URL = 'http://localhost:8000/api/v1'

export default function Dashboard() {
  const { token } = useAuthStore()

  // Fetch cost summary
  const { data: costSummary, isLoading: summaryLoading } = useQuery({
    queryKey: ['costSummary'],
    queryFn: async () => {
      const response = await costsApi.getSummary()
      return response.data
    },
    retry: 1
  })

  // Fetch cost trend
  const { data: costTrend, isLoading: trendLoading } = useQuery({
    queryKey: ['costTrend'],
    queryFn: async () => {
      const response = await costsApi.getTrend()
      return response.data
    },
    retry: 1
  })

  // Fetch multi-account summary
  const { data: multiAccount, isLoading: multiAccountLoading } = useQuery({
    queryKey: ['multiAccount'],
    queryFn: async () => {
      const response = await costsApi.getMultiAccount()
      return response.data
    },
    retry: 1
  })

  // Fetch budgets
  const { data: budgetsData } = useQuery({
    queryKey: ['budgets'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/budgets/`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      return response.data
    },
    enabled: !!token,
    retry: 1
  })

  const totalCost = costSummary?.total_cost || 0
  const topServices = costSummary?.breakdown?.slice(0, 5) || []
  const accounts = multiAccount?.accounts || []

  // Filter budgets with alerts
  const budgets = budgetsData?.budgets || []
  const budgetAlerts = budgets.filter((b: any) => b.is_over_threshold || b.is_over_budget)

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {/* Total Cost Card */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Total Monthly Cost</h3>
          {summaryLoading ? (
            <div className="h-10 bg-gray-200 animate-pulse rounded"></div>
          ) : (
            <>
              <p className="text-3xl font-bold text-gray-900">${totalCost.toFixed(2)}</p>
              <p className="text-sm text-gray-500 mt-2">Last 30 days</p>
            </>
          )}
        </div>

        {/* Top Service Card */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Top Service</h3>
          {summaryLoading ? (
            <div className="h-10 bg-gray-200 animate-pulse rounded"></div>
          ) : topServices.length > 0 ? (
            <>
              <p className="text-2xl font-bold text-gray-900">{topServices[0].service}</p>
              <p className="text-sm text-gray-500 mt-2">${topServices[0].cost.toFixed(2)} ({topServices[0].percentage}%)</p>
            </>
          ) : (
            <>
              <p className="text-2xl font-bold text-gray-900">N/A</p>
              <p className="text-sm text-gray-500 mt-2">No data</p>
            </>
          )}
        </div>

        {/* Services Count Card */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Active Services</h3>
          {summaryLoading ? (
            <div className="h-10 bg-gray-200 animate-pulse rounded"></div>
          ) : (
            <>
              <p className="text-3xl font-bold text-gray-900">{costSummary?.breakdown?.length || 0}</p>
              <p className="text-sm text-gray-500 mt-2">AWS services in use</p>
            </>
          )}
        </div>
      </div>

      {/* Budget Alerts */}
      {budgetAlerts.length > 0 && (
        <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="text-yellow-600" size={24} />
              <h3 className="text-lg font-semibold text-gray-900">Budget Alerts</h3>
            </div>
            <Link
              to="/budgets"
              className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
            >
              View All Budgets →
            </Link>
          </div>
          <div className="space-y-3">
            {budgetAlerts.map((budget: any) => (
              <div
                key={budget.id}
                className={`bg-white rounded-lg p-4 border-l-4 ${
                  budget.is_over_budget
                    ? 'border-red-500'
                    : 'border-yellow-500'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {budget.is_over_budget ? (
                        <span className="text-red-600 font-semibold">🔴</span>
                      ) : (
                        <span className="text-yellow-600 font-semibold">🟡</span>
                      )}
                      <h4 className="font-semibold text-gray-900">{budget.name}</h4>
                      <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                        budget.is_over_budget
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {budget.is_over_budget ? 'Over Budget' : 'Over Threshold'}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span>
                        <strong>${(budget.current_spend || 0).toFixed(2)}</strong> of ${budget.budget_amount.toFixed(2)}
                      </span>
                      <span>•</span>
                      <span>
                        <strong>{(budget.percentage_used || 0).toFixed(1)}%</strong> used
                      </span>
                      <span>•</span>
                      <span>{budget.days_remaining || 0} days remaining</span>
                    </div>
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          budget.is_over_budget ? 'bg-red-600' : 'bg-yellow-500'
                        }`}
                        style={{ width: `${Math.min(budget.percentage_used || 0, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cost Trend Chart */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Cost Trend (Last 30 Days)</h3>
        {trendLoading ? (
          <div className="h-64 bg-gray-200 animate-pulse rounded"></div>
        ) : costTrend && costTrend.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={costTrend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis
                tickFormatter={(value) => `$${value.toFixed(0)}`}
              />
              <Tooltip
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Cost']}
                labelFormatter={(label) => new Date(label).toLocaleDateString()}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="cost"
                stroke="#0ea5e9"
                strokeWidth={2}
                dot={false}
                name="Daily Cost"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-64 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="mb-2">No cost data available</p>
              <p className="text-sm">Link an AWS account and sync cost data to get started</p>
            </div>
          </div>
        )}
      </div>

      {/* Top Services Breakdown */}
      {!summaryLoading && topServices.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top 5 Services by Cost</h3>
          <div className="space-y-3">
            {topServices.map((service, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{service.service}</span>
                    <span className="text-sm font-semibold text-gray-900">${service.cost.toFixed(2)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full"
                      style={{ width: `${service.percentage}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Multi-Account Summary */}
      {!multiAccountLoading && accounts.length > 1 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cost by AWS Account</h3>
          <div className="space-y-3">
            {accounts.map((account, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <div>
                      <span className="text-sm font-medium text-gray-700">{account.account_name}</span>
                      <span className="text-xs text-gray-500 ml-2">({account.aws_account_id})</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">${account.cost.toFixed(2)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${account.percentage}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Total across {accounts.length} accounts</span>
              <span className="text-lg font-bold text-gray-900">${multiAccount?.total_cost.toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
