import { useState, useCallback, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Background,
  Controls,
  MiniMap,
  Connection,
  NodeChange,
  EdgeChange,
  applyNodeChanges,
  applyEdgeChanges,
  Panel
} from 'reactflow'
import 'reactflow/dist/style.css'
import { AWS_SERVICES, AWSService, calculateServiceCost, getServicesByCategory } from '@/lib/awsServices'
import { architecturesApi } from '@/lib/api'
import SaveArchitectureDialog from '@/components/SaveArchitectureDialog'
import { exportToCloudFormation, exportToTerraform, downloadFile } from '@/lib/architectureExport'
import { AWS_REGIONS, getAvailabilityZones, getRegionColor, Region } from '@/lib/regionalPricing'
import { Save, FolderOpen, Trash2, Download, Share2, FileCode, Globe, Layers } from 'lucide-react'

interface ServiceNodeData {
  service: AWSService
  config: { [key: string]: any }
  label: string
  region: string
  availabilityZone?: string
}

export default function ArchitectureDesigner() {
  const queryClient = useQueryClient()
  const [nodes, setNodes] = useState<Node<ServiceNodeData>[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [selectedNode, setSelectedNode] = useState<Node<ServiceNodeData> | null>(null)
  const [showServicePalette, setShowServicePalette] = useState(true)
  const [showSavedList, setShowSavedList] = useState(false)
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [showExportMenu, setShowExportMenu] = useState(false)
  const [showShareDialog, setShowShareDialog] = useState(false)
  const [currentArchitectureId, setCurrentArchitectureId] = useState<string | null>(null)
  const [currentArchitectureName, setCurrentArchitectureName] = useState('')
  const [currentArchitectureDesc, setCurrentArchitectureDesc] = useState('')
  const [defaultRegion, setDefaultRegion] = useState<string>('us-east-1')
  const [showRegionPanel, setShowRegionPanel] = useState(false)
  const [showCostBreakdown, setShowCostBreakdown] = useState(false)

  const servicesByCategory = useMemo(() => getServicesByCategory(), [])

  // Fetch saved architectures
  const { data: savedArchitectures, isLoading: loadingArchitectures } = useQuery({
    queryKey: ['architectures'],
    queryFn: async () => {
      const response = await architecturesApi.list()
      return response.data
    }
  })

  // Save architecture mutation
  const saveMutation = useMutation({
    mutationFn: async ({ name, description }: { name: string; description: string }) => {
      const data = {
        name,
        description,
        nodes,
        edges,
        estimated_monthly_cost: totalCost.toFixed(2)
      }

      if (currentArchitectureId) {
        return await architecturesApi.update(currentArchitectureId, data)
      } else {
        return await architecturesApi.create(data)
      }
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['architectures'] })
      setCurrentArchitectureId(response.data.id)
      setCurrentArchitectureName(response.data.name)
      setCurrentArchitectureDesc(response.data.description || '')
      alert('Architecture saved successfully!')
    },
    onError: (error: any) => {
      console.error('Error saving architecture:', error)
      alert(error.response?.data?.detail || 'Failed to save architecture')
    }
  })

  // Delete architecture mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => architecturesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['architectures'] })
      alert('Architecture deleted successfully!')
    }
  })

  // Calculate total cost of all services in the architecture
  const totalCost = useMemo(() => {
    return nodes.reduce((sum, node) => {
      const service = node.data.service
      const config = node.data.config
      const region = node.data.region || 'us-east-1'
      return sum + calculateServiceCost(service, config, region)
    }, 0)
  }, [nodes])

  // Calculate cost breakdown by region
  const costByRegion = useMemo(() => {
    const breakdown: { [region: string]: number } = {}
    nodes.forEach(node => {
      const region = node.data.region || 'us-east-1'
      const cost = calculateServiceCost(node.data.service, node.data.config, region)
      breakdown[region] = (breakdown[region] || 0) + cost
    })
    return breakdown
  }, [nodes])

  // Get unique regions used in architecture
  const usedRegions = useMemo(() => {
    const regions = new Set(nodes.map(n => n.data.region || 'us-east-1'))
    return Array.from(regions)
  }, [nodes])

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  )

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  )

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
    []
  )

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node<ServiceNodeData>) => {
    setSelectedNode(node)
  }, [])

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  // Update node region
  const updateNodeRegion = useCallback((nodeId: string, region: string, availabilityZone?: string) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: { ...node.data, region, availabilityZone },
            style: {
              ...node.style,
              borderColor: getRegionColor(region),
            }
          }
        }
        return node
      })
    )
  }, [])

  // Add a service to the canvas
  const addServiceToCanvas = useCallback((service: AWSService, region?: string) => {
    const selectedRegion = region || defaultRegion
    const regionColor = getRegionColor(selectedRegion)

    const newNode: Node<ServiceNodeData> = {
      id: `${service.id}-${Date.now()}`,
      type: 'default',
      position: { x: 250 + Math.random() * 200, y: 100 + Math.random() * 200 },
      data: {
        service,
        config: service.configurableOptions.reduce((acc, opt) => {
          acc[opt.id] = opt.default
          return acc
        }, {} as { [key: string]: any }),
        label: service.name,
        region: selectedRegion,
        availabilityZone: undefined // Can be set later
      },
      style: {
        background: service.color,
        color: '#fff',
        borderWidth: 3,
        borderColor: regionColor,
        borderStyle: 'solid',
        border: '2px solid #fff',
        borderRadius: '8px',
        padding: '10px',
        fontSize: '12px',
        fontWeight: 'bold',
        width: 180
      }
    }

    setNodes((nds) => [...nds, newNode])
  }, [])

  // Update node configuration
  const updateNodeConfig = useCallback((nodeId: string, configKey: string, value: any) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: {
              ...node.data,
              config: {
                ...node.data.config,
                [configKey]: value
              }
            }
          }
        }
        return node
      })
    )
  }, [])

  // Delete selected node
  const deleteSelectedNode = useCallback(() => {
    if (selectedNode) {
      setNodes((nds) => nds.filter((node) => node.id !== selectedNode.id))
      setEdges((eds) => eds.filter((edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id))
      setSelectedNode(null)
    }
  }, [selectedNode])

  // Clear entire canvas
  const clearCanvas = useCallback(() => {
    if (window.confirm('Are you sure you want to clear the entire architecture? This cannot be undone.')) {
      setNodes([])
      setEdges([])
      setSelectedNode(null)
      setCurrentArchitectureId(null)
      setCurrentArchitectureName('')
      setCurrentArchitectureDesc('')
    }
  }, [])

  // Load an architecture
  const loadArchitecture = useCallback((architecture: any) => {
    setNodes(architecture.nodes || [])
    setEdges(architecture.edges || [])
    setCurrentArchitectureId(architecture.id)
    setCurrentArchitectureName(architecture.name)
    setCurrentArchitectureDesc(architecture.description || '')
    setSelectedNode(null)
    setShowSavedList(false)
  }, [])

  // Handle save
  const handleSave = async (name: string, description: string) => {
    await saveMutation.mutateAsync({ name, description })
  }

  // Handle delete
  const handleDelete = (id: string) => {
    if (window.confirm('Are you sure you want to delete this architecture?')) {
      deleteMutation.mutate(id)
      if (currentArchitectureId === id) {
        clearCanvas()
      }
    }
  }

  // Create new architecture
  const createNew = () => {
    if (nodes.length > 0 || edges.length > 0) {
      if (!window.confirm('Current work will be cleared. Continue?')) {
        return
      }
    }
    clearCanvas()
  }

  // Export handlers
  const handleExportCloudFormation = () => {
    if (nodes.length === 0) {
      alert('Add some services to the canvas before exporting')
      return
    }
    const cfTemplate = exportToCloudFormation(
      nodes,
      edges,
      currentArchitectureName || 'My Architecture'
    )
    downloadFile(
      cfTemplate,
      `${currentArchitectureName || 'architecture'}-cloudformation.json`,
      'application/json'
    )
    setShowExportMenu(false)
  }

  const handleExportTerraform = () => {
    if (nodes.length === 0) {
      alert('Add some services to the canvas before exporting')
      return
    }
    const tfConfig = exportToTerraform(
      nodes,
      edges,
      currentArchitectureName || 'My Architecture'
    )
    downloadFile(
      tfConfig,
      `${currentArchitectureName || 'architecture'}.tf`,
      'text/plain'
    )
    setShowExportMenu(false)
  }

  // Share/toggle public mutation
  const togglePublicMutation = useMutation({
    mutationFn: async (isPublic: boolean) => {
      if (!currentArchitectureId) {
        throw new Error('No architecture selected')
      }
      return await architecturesApi.update(currentArchitectureId, { is_public: isPublic })
    },
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['architectures'] })
      alert(response.data.is_public ? 'Architecture is now public' : 'Architecture is now private')
      setShowShareDialog(false)
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to update sharing settings')
    }
  })

  const handleTogglePublic = (isPublic: boolean) => {
    togglePublicMutation.mutate(isPublic)
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex">
      {/* Service Palette */}
      <div
        className={`${
          showServicePalette ? 'w-64' : 'w-0'
        } transition-all duration-300 bg-white border-r border-gray-200 overflow-y-auto`}
      >
        {showServicePalette && (
          <div className="p-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">AWS Services</h3>
              <button
                onClick={() => setShowServicePalette(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            {Object.entries(servicesByCategory).map(([category, services]) => (
              <div key={category} className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">{category}</h4>
                <div className="space-y-2">
                  {services.map((service) => (
                    <button
                      key={service.id}
                      onClick={() => addServiceToCanvas(service)}
                      className="w-full text-left p-2 rounded border border-gray-200 hover:border-primary-500 hover:bg-primary-50 transition-colors"
                      style={{ borderLeftColor: service.color, borderLeftWidth: '4px' }}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{service.icon}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">{service.name}</p>
                          <p className="text-xs text-gray-500">${service.basePrice.toFixed(2)}/mo</p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Canvas */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          fitView
        >
          <Background />
          <Controls />
          <MiniMap />

          {/* Top Toolbar */}
          <Panel position="top-left" className="flex gap-2 flex-wrap">
            {!showServicePalette && (
              <button
                onClick={() => setShowServicePalette(true)}
                className="px-3 py-2 bg-white rounded shadow-md text-sm font-medium text-gray-700 hover:bg-gray-50 border border-gray-200"
              >
                Show Services
              </button>
            )}
            <button
              onClick={createNew}
              className="px-3 py-2 bg-white rounded shadow-md text-sm font-medium text-gray-700 hover:bg-gray-50 border border-gray-200"
            >
              New
            </button>
            <button
              onClick={() => setShowSaveDialog(true)}
              className="px-3 py-2 bg-primary-600 text-white rounded shadow-md text-sm font-medium hover:bg-primary-700 flex items-center gap-1"
            >
              <Save className="w-4 h-4" />
              {currentArchitectureId ? 'Update' : 'Save'}
            </button>
            <button
              onClick={() => setShowSavedList(!showSavedList)}
              className="px-3 py-2 bg-white rounded shadow-md text-sm font-medium text-gray-700 hover:bg-gray-50 border border-gray-200 flex items-center gap-1"
            >
              <FolderOpen className="w-4 h-4" />
              Load ({savedArchitectures?.total || 0})
            </button>

            {/* Export Button with Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                disabled={nodes.length === 0}
                className="px-3 py-2 bg-white rounded shadow-md text-sm font-medium text-gray-700 hover:bg-gray-50 border border-gray-200 flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
              {showExportMenu && (
                <div className="absolute top-full left-0 mt-1 bg-white rounded shadow-lg border border-gray-200 z-10 min-w-[200px]">
                  <button
                    onClick={handleExportCloudFormation}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                  >
                    <FileCode className="w-4 h-4" />
                    CloudFormation (JSON)
                  </button>
                  <button
                    onClick={handleExportTerraform}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2 border-t border-gray-100"
                  >
                    <FileCode className="w-4 h-4" />
                    Terraform (HCL)
                  </button>
                </div>
              )}
            </div>

            {/* Share Button */}
            <button
              onClick={() => setShowShareDialog(true)}
              disabled={!currentArchitectureId}
              className="px-3 py-2 bg-white rounded shadow-md text-sm font-medium text-gray-700 hover:bg-gray-50 border border-gray-200 flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Share2 className="w-4 h-4" />
              Share
            </button>

            <button
              onClick={clearCanvas}
              className="px-3 py-2 bg-white rounded shadow-md text-sm font-medium text-red-700 hover:bg-red-50 border border-red-200"
            >
              Clear
            </button>

            {/* Region Selector */}
            <div className="relative">
              <button
                onClick={() => setShowRegionPanel(!showRegionPanel)}
                className="px-3 py-2 bg-white rounded shadow-md text-sm font-medium text-gray-700 hover:bg-gray-50 border border-gray-200 flex items-center gap-1"
              >
                <Globe className="w-4 h-4" />
                {AWS_REGIONS.find(r => r.code === defaultRegion)?.name.split(' ')[0] || 'Region'}
              </button>
              {showRegionPanel && (
                <div className="absolute top-full left-0 mt-1 bg-white rounded shadow-lg border border-gray-200 z-10 max-h-96 overflow-y-auto" style={{ minWidth: '250px' }}>
                  <div className="p-2 border-b border-gray-200">
                    <p className="text-xs font-medium text-gray-700">Default Region for New Services</p>
                  </div>
                  {AWS_REGIONS.map((region) => (
                    <button
                      key={region.code}
                      onClick={() => {
                        setDefaultRegion(region.code)
                        setShowRegionPanel(false)
                      }}
                      className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center justify-between ${
                        defaultRegion === region.code ? 'bg-primary-50 text-primary-700' : 'text-gray-700'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: getRegionColor(region.code) }}
                        />
                        <span>{region.name}</span>
                      </div>
                      {defaultRegion === region.code && <span className="text-xs">✓</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Cost Breakdown Toggle */}
            <button
              onClick={() => setShowCostBreakdown(!showCostBreakdown)}
              disabled={usedRegions.length === 0}
              className="px-3 py-2 bg-white rounded shadow-md text-sm font-medium text-gray-700 hover:bg-gray-50 border border-gray-200 flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Layers className="w-4 h-4" />
              Costs by Region
            </button>
          </Panel>

          {/* Cost Display */}
          <Panel position="top-right" className="bg-white rounded shadow-md p-4 border border-gray-200">
            {currentArchitectureName && (
              <div className="mb-2 pb-2 border-b border-gray-200">
                <p className="text-xs font-medium text-gray-500">Current</p>
                <p className="text-sm font-semibold text-gray-900 truncate">{currentArchitectureName}</p>
              </div>
            )}
            <h3 className="text-sm font-medium text-gray-700 mb-1">Estimated Monthly Cost</h3>
            <p className="text-2xl font-bold text-primary-600">${totalCost.toFixed(2)}</p>
            <p className="text-xs text-gray-500 mt-1">{nodes.length} service(s)</p>
          </Panel>

          {/* Regional Cost Breakdown Panel */}
          {showCostBreakdown && usedRegions.length > 0 && (
            <Panel position="bottom-left" className="bg-white rounded shadow-lg p-4 border border-gray-200 max-w-sm w-full">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-sm font-semibold text-gray-900">Cost by Region</h3>
                <button
                  onClick={() => setShowCostBreakdown(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              <div className="space-y-2">
                {usedRegions.map((regionCode) => {
                  const region = AWS_REGIONS.find(r => r.code === regionCode)
                  const cost = costByRegion[regionCode] || 0
                  const percentage = (cost / totalCost) * 100

                  return (
                    <div key={regionCode} className="border-b border-gray-100 pb-2 last:border-b-0">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: getRegionColor(regionCode) }}
                          />
                          <span className="text-sm font-medium text-gray-900">
                            {region?.name || regionCode}
                          </span>
                        </div>
                        <span className="text-sm font-semibold text-gray-900">
                          ${cost.toFixed(2)}
                        </span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-2">
                        <div
                          className="h-2 rounded-full transition-all"
                          style={{
                            width: `${percentage}%`,
                            backgroundColor: getRegionColor(regionCode)
                          }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {percentage.toFixed(1)}% of total cost
                      </p>
                    </div>
                  )
                })}
              </div>
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">Total</span>
                  <span className="text-lg font-bold text-primary-600">${totalCost.toFixed(2)}</span>
                </div>
              </div>
            </Panel>
          )}

          {/* Saved Architectures List */}
          {showSavedList && (
            <Panel position="top-center" className="bg-white rounded shadow-lg p-4 border border-gray-200 max-w-md w-full max-h-96 overflow-y-auto">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-semibold text-gray-900">Saved Architectures</h3>
                <button
                  onClick={() => setShowSavedList(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              {loadingArchitectures ? (
                <p className="text-sm text-gray-500">Loading...</p>
              ) : savedArchitectures?.architectures.length === 0 ? (
                <p className="text-sm text-gray-500">No saved architectures</p>
              ) : (
                <div className="space-y-2">
                  {savedArchitectures?.architectures.map((arch: any) => (
                    <div
                      key={arch.id}
                      className="p-3 border border-gray-200 rounded hover:border-primary-500 transition-colors"
                    >
                      <div className="flex justify-between items-start">
                        <button
                          onClick={() => loadArchitecture(arch)}
                          className="flex-1 text-left"
                        >
                          <p className="font-medium text-gray-900">{arch.name}</p>
                          {arch.description && (
                            <p className="text-xs text-gray-500 mt-1">{arch.description}</p>
                          )}
                          <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                            <span>${arch.estimated_monthly_cost || '0.00'}/mo</span>
                            <span>{new Date(arch.updated_at).toLocaleDateString()}</span>
                          </div>
                        </button>
                        <button
                          onClick={() => handleDelete(arch.id)}
                          className="ml-2 text-red-600 hover:text-red-800"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Panel>
          )}
        </ReactFlow>
      </div>

      {/* Configuration Panel */}
      {selectedNode && (
        <div className="w-80 bg-white border-l border-gray-200 overflow-y-auto">
          <div className="p-4">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {selectedNode.data.service.icon} {selectedNode.data.service.name}
                </h3>
                <p className="text-sm text-gray-500">{selectedNode.data.service.description}</p>
              </div>
              <button
                onClick={deleteSelectedNode}
                className="text-red-600 hover:text-red-800 text-sm font-medium"
              >
                Delete
              </button>
            </div>

            {/* Region & Availability Zone */}
            <div className="mb-4 space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Globe className="w-4 h-4 inline mr-1" />
                  Region
                </label>
                <select
                  value={selectedNode.data.region || 'us-east-1'}
                  onChange={(e) => {
                    updateNodeRegion(selectedNode.id, e.target.value, undefined)
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  {AWS_REGIONS.map((region) => (
                    <option key={region.code} value={region.code}>
                      {region.name}
                    </option>
                  ))}
                </select>
                <div className="mt-1 flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: getRegionColor(selectedNode.data.region || 'us-east-1') }}
                  />
                  <p className="text-xs text-gray-500">
                    Price multiplier: {AWS_REGIONS.find(r => r.code === (selectedNode.data.region || 'us-east-1'))?.priceMultiplier.toFixed(2)}x
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Availability Zone (Optional)
                </label>
                <select
                  value={selectedNode.data.availabilityZone || ''}
                  onChange={(e) => {
                    updateNodeRegion(
                      selectedNode.id,
                      selectedNode.data.region || 'us-east-1',
                      e.target.value || undefined
                    )
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="">Auto (any AZ)</option>
                  {getAvailabilityZones(selectedNode.data.region || 'us-east-1').map((az) => (
                    <option key={az} value={az}>
                      {az}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Base Price */}
            <div className="mb-4 p-3 bg-gray-50 rounded">
              <p className="text-sm text-gray-600">Base Price (in {selectedNode.data.region || 'us-east-1'})</p>
              <p className="text-lg font-semibold text-gray-900">
                ${calculateServiceCost(selectedNode.data.service, {}, selectedNode.data.region || 'us-east-1').toFixed(2)}
              </p>
              <p className="text-xs text-gray-500">{selectedNode.data.service.pricingUnit}</p>
            </div>

            {/* Configuration Options */}
            {selectedNode.data.service.configurableOptions.length > 0 && (
              <div className="space-y-4">
                <h4 className="text-sm font-medium text-gray-700">Configuration</h4>

                {selectedNode.data.service.configurableOptions.map((option) => (
                  <div key={option.id}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {option.label}
                    </label>

                    {option.type === 'number' && (
                      <input
                        type="number"
                        value={selectedNode.data.config[option.id]}
                        onChange={(e) =>
                          updateNodeConfig(selectedNode.id, option.id, parseInt(e.target.value) || 0)
                        }
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                        min="0"
                      />
                    )}

                    {option.type === 'select' && option.options && (
                      <select
                        value={selectedNode.data.config[option.id]}
                        onChange={(e) => updateNodeConfig(selectedNode.id, option.id, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      >
                        {option.options.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    )}

                    {option.type === 'toggle' && (
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedNode.data.config[option.id]}
                          onChange={(e) =>
                            updateNodeConfig(selectedNode.id, option.id, e.target.checked)
                          }
                          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                        />
                        <span className="ml-2 text-sm text-gray-600">Enabled</span>
                      </label>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Calculated Cost */}
            <div className="mt-6 p-3 bg-primary-50 rounded border border-primary-200">
              <p className="text-sm text-gray-600">Total Cost (in {selectedNode.data.region || 'us-east-1'})</p>
              <p className="text-xl font-bold text-primary-600">
                ${calculateServiceCost(selectedNode.data.service, selectedNode.data.config, selectedNode.data.region || 'us-east-1').toFixed(2)}
                <span className="text-sm font-normal text-gray-500">/month</span>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Save Architecture Dialog */}
      <SaveArchitectureDialog
        isOpen={showSaveDialog}
        onClose={() => setShowSaveDialog(false)}
        onSave={handleSave}
        existingName={currentArchitectureName}
        existingDescription={currentArchitectureDesc}
      />

      {/* Share Architecture Dialog */}
      {showShareDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Share Architecture</h2>
              <button
                onClick={() => setShowShareDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="mb-6">
              <p className="text-sm text-gray-600 mb-4">
                Make this architecture public so others can view it. Public architectures can be
                discovered and viewed by other users.
              </p>

              {currentArchitectureName && (
                <div className="p-3 bg-gray-50 rounded mb-4">
                  <p className="text-sm font-medium text-gray-900">{currentArchitectureName}</p>
                  {currentArchitectureDesc && (
                    <p className="text-xs text-gray-600 mt-1">{currentArchitectureDesc}</p>
                  )}
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => handleTogglePublic(false)}
                disabled={togglePublicMutation.isPending}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Make Private
              </button>
              <button
                onClick={() => handleTogglePublic(true)}
                disabled={togglePublicMutation.isPending}
                className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
              >
                {togglePublicMutation.isPending ? 'Updating...' : 'Make Public'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
