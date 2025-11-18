import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { costsApi } from '@/lib/api'
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const COLORS = ['#0ea5e9', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#ef4444']

export default function CostExplorer() {
  const [dateRange, setDateRange] = useState<{ start: string; end: string }>({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  })

  // Fetch cost by region
  const { data: regionData, isLoading: regionLoading } = useQuery({
    queryKey: ['costByRegion', dateRange],
    queryFn: async () => {
      const response = await costsApi.getByRegion({
        start_date: dateRange.start,
        end_date: dateRange.end
      })
      return response.data
    },
    retry: 1
  })

  // Fetch month-over-month comparison
  const { data: monthComparison, isLoading: comparisonLoading } = useQuery({
    queryKey: ['monthComparison'],
    queryFn: async () => {
      const response = await costsApi.getMonthComparison()
      return response.data
    },
    retry: 1
  })

  // Fetch cost trend
  const { data: costTrend, isLoading: trendLoading } = useQuery({
    queryKey: ['costTrend', dateRange],
    queryFn: async () => {
      const response = await costsApi.getTrend({
        start_date: dateRange.start,
        end_date: dateRange.end
      })
      return response.data
    },
    retry: 1
  })

  const handleDateRangeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setDateRange(prev => ({ ...prev, [name]: value }))
  }

  const setPresetRange = (days: number) => {
    const end = new Date()
    const start = new Date(Date.now() - days * 24 * 60 * 60 * 1000)
    setDateRange({
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0]
    })
  }

  const regionBreakdown = regionData?.breakdown || []
  const hasCostData = regionBreakdown.length > 0 || (costTrend && costTrend.length > 0)

  const handleExportCSV = async () => {
    try {
      const token = localStorage.getItem('token')
      const params = new URLSearchParams({
        start_date: dateRange.start,
        end_date: dateRange.end
      })

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/costs/export/csv?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `cloudcostly_costs_${dateRange.start}_${dateRange.end}.csv`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Error exporting CSV:', error)
    }
  }

  const handleExportPDF = async () => {
    try {
      const token = localStorage.getItem('token')
      const params = new URLSearchParams({
        start_date: dateRange.start,
        end_date: dateRange.end
      })

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/costs/export/pdf?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `cloudcostly_report_${dateRange.start}_${dateRange.end}.pdf`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Error exporting PDF:', error)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Cost Explorer</h1>
        {hasCostData && (
          <div className="flex gap-2">
            <button
              onClick={handleExportCSV}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
            >
              Export CSV
            </button>
            <button
              onClick={handleExportPDF}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Export PDF
            </button>
          </div>
        )}
      </div>

      {/* Date Range Selector */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Start Date:</label>
            <input
              type="date"
              name="start"
              value={dateRange.start}
              onChange={handleDateRangeChange}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">End Date:</label>
            <input
              type="date"
              name="end"
              value={dateRange.end}
              onChange={handleDateRangeChange}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPresetRange(7)}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Last 7 Days
            </button>
            <button
              onClick={() => setPresetRange(30)}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Last 30 Days
            </button>
            <button
              onClick={() => setPresetRange(90)}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Last 90 Days
            </button>
          </div>
        </div>
      </div>

      {!hasCostData ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="text-center text-gray-500">
            <p className="mb-4">No cost data available</p>
            <p className="text-sm">Link an AWS account and sync cost data to explore your costs</p>
          </div>
        </div>
      ) : (
        <>
          {/* Month-over-Month Comparison */}
          {!comparisonLoading && monthComparison && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500 mb-2">Current Month</h3>
                <p className="text-3xl font-bold text-gray-900">
                  ${monthComparison.current_month.total_cost.toFixed(2)}
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  {new Date(monthComparison.current_month.start_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                </p>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500 mb-2">Previous Month</h3>
                <p className="text-3xl font-bold text-gray-900">
                  ${monthComparison.previous_month.total_cost.toFixed(2)}
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  {new Date(monthComparison.previous_month.start_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                </p>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-sm font-medium text-gray-500 mb-2">Month-over-Month Change</h3>
                <p className={`text-3xl font-bold ${
                  monthComparison.change.trend === 'up' ? 'text-red-600' :
                  monthComparison.change.trend === 'down' ? 'text-green-600' :
                  'text-gray-900'
                }`}>
                  {monthComparison.change.trend === 'up' ? '+' : ''}
                  {monthComparison.change.percentage.toFixed(1)}%
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  ${Math.abs(monthComparison.change.amount).toFixed(2)} {monthComparison.change.trend}
                </p>
              </div>
            </div>
          )}

          {/* Cost Trend Chart */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Cost Trend</h3>
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
                  <YAxis tickFormatter={(value) => `$${value.toFixed(0)}`} />
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
                No trend data available
              </div>
            )}
          </div>

          {/* Cost by Region */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pie Chart */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Cost by Region</h3>
              {regionLoading ? (
                <div className="h-64 bg-gray-200 animate-pulse rounded"></div>
              ) : regionBreakdown.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={regionBreakdown}
                      dataKey="cost"
                      nameKey="region"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={(entry) => `${entry.region}: $${entry.cost.toFixed(2)}`}
                    >
                      {regionBreakdown.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500">
                  No region data available
                </div>
              )}
            </div>

            {/* Bar Chart */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Region Breakdown</h3>
              {regionLoading ? (
                <div className="h-64 bg-gray-200 animate-pulse rounded"></div>
              ) : regionBreakdown.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={regionBreakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="region" />
                    <YAxis tickFormatter={(value) => `$${value.toFixed(0)}`} />
                    <Tooltip formatter={(value: number) => [`$${value.toFixed(2)}`, 'Cost']} />
                    <Legend />
                    <Bar dataKey="cost" fill="#0ea5e9" name="Cost" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500">
                  No region data available
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
