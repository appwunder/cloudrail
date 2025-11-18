import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Edit2, Trash2, DollarSign, AlertTriangle, TrendingUp, Calendar } from "lucide-react";
import axios from "axios";
import { useAuthStore } from "../store/authStore";

const API_URL = "http://localhost:8000/api/v1";

interface Budget {
  id: string;
  name: string;
  description: string | null;
  budget_amount: number;
  period: "daily" | "weekly" | "monthly" | "quarterly" | "annually";
  account_id: string | null;
  service_name: string | null;
  region: string | null;
  threshold_percentage: number;
  notification_channels: string[];
  notification_emails: string[] | null;
  slack_webhook_url: string | null;
  custom_webhook_url: string | null;
  is_active: boolean;
  current_spend?: number;
  percentage_used?: number;
  days_remaining?: number;
  is_over_budget?: boolean;
  is_over_threshold?: boolean;
  created_at: string;
  updated_at: string;
}

interface BudgetForm {
  name: string;
  description: string;
  budget_amount: number;
  period: string;
  threshold_percentage: number;
  notification_channels: string[];
  notification_emails: string;
  is_active: boolean;
}

export default function Budgets() {
  const { token } = useAuthStore();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingBudget, setEditingBudget] = useState<Budget | null>(null);
  const [formData, setFormData] = useState<BudgetForm>({
    name: "",
    description: "",
    budget_amount: 1000,
    period: "monthly",
    threshold_percentage: 80,
    notification_channels: ["email"],
    notification_emails: "",
    is_active: true,
  });

  // Fetch budgets
  const { data: budgetsData, isLoading } = useQuery({
    queryKey: ["budgets"],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/budgets/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    },
    enabled: !!token,
  });

  // Create budget mutation
  const createBudget = useMutation({
    mutationFn: async (data: any) => {
      const response = await axios.post(`${API_URL}/budgets/`, data, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      setShowCreateModal(false);
      resetForm();
    },
  });

  // Update budget mutation
  const updateBudget = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const response = await axios.put(`${API_URL}/budgets/${id}`, data, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
      setEditingBudget(null);
      resetForm();
    },
  });

  // Delete budget mutation
  const deleteBudget = useMutation({
    mutationFn: async (id: string) => {
      await axios.delete(`${API_URL}/budgets/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      budget_amount: 1000,
      period: "monthly",
      threshold_percentage: 80,
      notification_channels: ["email"],
      notification_emails: "",
      is_active: true,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const submitData = {
      ...formData,
      notification_emails: formData.notification_emails
        ? formData.notification_emails.split(",").map((e) => e.trim())
        : [],
    };

    if (editingBudget) {
      updateBudget.mutate({ id: editingBudget.id, data: submitData });
    } else {
      createBudget.mutate(submitData);
    }
  };

  const handleEdit = (budget: Budget) => {
    setEditingBudget(budget);
    setFormData({
      name: budget.name,
      description: budget.description || "",
      budget_amount: budget.budget_amount,
      period: budget.period,
      threshold_percentage: budget.threshold_percentage,
      notification_channels: budget.notification_channels,
      notification_emails: budget.notification_emails?.join(", ") || "",
      is_active: budget.is_active,
    });
    setShowCreateModal(true);
  };

  const handleDelete = (id: string) => {
    if (confirm("Are you sure you want to delete this budget?")) {
      deleteBudget.mutate(id);
    }
  };

  const budgets: Budget[] = budgetsData?.budgets || [];
  const totalBudgets = budgets.length;
  const activeBudgets = budgets.filter((b) => b.is_active).length;
  const overBudget = budgets.filter((b) => b.is_over_budget).length;
  const overThreshold = budgets.filter((b) => b.is_over_threshold && !b.is_over_budget).length;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Budget Management</h1>
          <p className="text-gray-600 mt-1">Set budgets and receive alerts when spending exceeds thresholds</p>
        </div>
        <button
          onClick={() => {
            setEditingBudget(null);
            resetForm();
            setShowCreateModal(true);
          }}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
        >
          <Plus size={20} />
          Create Budget
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Total Budgets</p>
              <p className="text-2xl font-bold text-gray-900">{totalBudgets}</p>
            </div>
            <DollarSign className="text-indigo-600" size={32} />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Active Budgets</p>
              <p className="text-2xl font-bold text-green-600">{activeBudgets}</p>
            </div>
            <TrendingUp className="text-green-600" size={32} />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Over Threshold</p>
              <p className="text-2xl font-bold text-yellow-600">{overThreshold}</p>
            </div>
            <AlertTriangle className="text-yellow-600" size={32} />
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Over Budget</p>
              <p className="text-2xl font-bold text-red-600">{overBudget}</p>
            </div>
            <AlertTriangle className="text-red-600" size={32} />
          </div>
        </div>
      </div>

      {/* Budgets List */}
      <div className="bg-white rounded-lg shadow">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading budgets...</div>
        ) : budgets.length === 0 ? (
          <div className="p-8 text-center">
            <DollarSign className="mx-auto text-gray-400 mb-4" size={48} />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No budgets yet</h3>
            <p className="text-gray-600 mb-4">Create your first budget to start monitoring your cloud spending</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700"
            >
              Create Budget
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Budget Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Period
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Budget Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Current Spend
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {budgets.map((budget) => (
                  <tr key={budget.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium text-gray-900">{budget.name}</div>
                        {budget.description && (
                          <div className="text-sm text-gray-500">{budget.description}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Calendar size={16} className="text-gray-400" />
                        <span className="capitalize text-sm">{budget.period}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold">
                      ${budget.budget_amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm">
                        <div className="font-semibold">
                          ${(budget.current_spend || 0).toLocaleString()}
                        </div>
                        <div className="text-gray-500">
                          {(budget.percentage_used || 0).toFixed(1)}% used
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {budget.is_over_budget ? (
                        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                          🔴 Over Budget
                        </span>
                      ) : budget.is_over_threshold ? (
                        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                          🟡 Over Threshold
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                          🟢 On Track
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(budget)}
                          className="text-indigo-600 hover:text-indigo-800"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete(budget.id)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">
              {editingBudget ? "Edit Budget" : "Create New Budget"}
            </h2>
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Budget Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-600 focus:border-transparent"
                    placeholder="e.g., Monthly AWS Budget"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-600 focus:border-transparent"
                    rows={3}
                    placeholder="Optional description"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Budget Amount ($) *</label>
                    <input
                      type="number"
                      required
                      min="0"
                      step="0.01"
                      value={formData.budget_amount}
                      onChange={(e) => setFormData({ ...formData, budget_amount: parseFloat(e.target.value) })}
                      className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-600 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Period *</label>
                    <select
                      value={formData.period}
                      onChange={(e) => setFormData({ ...formData, period: e.target.value })}
                      className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-600 focus:border-transparent"
                    >
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                      <option value="quarterly">Quarterly</option>
                      <option value="annually">Annually</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Alert Threshold (%) *
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    max="100"
                    value={formData.threshold_percentage}
                    onChange={(e) => setFormData({ ...formData, threshold_percentage: parseInt(e.target.value) })}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-600 focus:border-transparent"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Alert when spending reaches this percentage of the budget
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notification Emails (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={formData.notification_emails}
                    onChange={(e) => setFormData({ ...formData, notification_emails: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-600 focus:border-transparent"
                    placeholder="email1@example.com, email2@example.com"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-600"
                  />
                  <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
                    Active
                  </label>
                </div>
              </div>

              <div className="flex justify-end gap-4 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingBudget(null);
                    resetForm();
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  {editingBudget ? "Update Budget" : "Create Budget"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
