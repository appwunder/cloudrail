import { Link } from 'react-router-dom'
import {
  TrendingDown,
  Shield,
  LineChart,
  Bell,
  Layers,
  ArrowRight,
  CheckCircle,
  Cloud,
  CloudCog,
  DollarSign,
  Boxes,
  Lightbulb,
  BarChart3,
  Globe,
  Zap,
  Lock,
  Users
} from 'lucide-react'
import CloudRailLogo from '@/components/CloudRailLogo'
import { useAuthStore } from '@/store/authStore'

export default function Landing() {
  const { isAuthenticated } = useAuthStore()
  const features = [
    {
      icon: CloudCog,
      title: 'Multi-Cloud Support',
      description: 'Unified cost management for AWS, Google Cloud, Azure, and Alibaba Cloud in one platform.',
    },
    {
      icon: TrendingDown,
      title: 'Cost Optimization',
      description: 'AI-powered recommendations help you identify and eliminate wasteful spending automatically.',
    },
    {
      icon: LineChart,
      title: 'Detailed Analytics',
      description: 'Deep dive into cost trends, forecasts, and breakdowns by service, region, and tags.',
    },
    {
      icon: Bell,
      title: 'Smart Budget Alerts',
      description: 'Set budgets with flexible thresholds and get instant alerts when spending exceeds limits.',
    },
    {
      icon: Boxes,
      title: 'Architecture Designer',
      description: 'Design and estimate costs for multi-region, multi-AZ cloud infrastructure before deployment.',
    },
    {
      icon: Lightbulb,
      title: 'Cost Recommendations',
      description: 'Get intelligent suggestions for rightsizing, reserved instances, and eliminating idle resources.',
    },
    {
      icon: BarChart3,
      title: 'Real-Time Tracking',
      description: 'Monitor your cloud spending in real-time with automatic cost data synchronization.',
    },
    {
      icon: Globe,
      title: 'Multi-Region Analysis',
      description: 'Compare costs across different regions and availability zones to optimize placement.',
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Multi-tenant architecture with complete data isolation and role-based access control.',
    },
  ]

  const benefits = [
    'Reduce cloud costs by up to 40%',
    'Multi-cloud account aggregation',
    'Real-time cost tracking & sync',
    'AWS, GCP, Azure & Alibaba support',
    'Customizable budgets and alerts',
    'Architecture cost estimation',
    'Multi-region cost comparison',
    'Export reports to CSV',
    '50+ cloud services catalog',
    'Rightsizing recommendations',
    'Idle resource detection',
    'Reserved instance analysis',
  ]

  const cloudProviders = [
    { name: 'AWS', color: '#FF9900', icon: '☁️' },
    { name: 'GCP', color: '#4285F4', icon: '🔵' },
    { name: 'Azure', color: '#0078D4', icon: '🔷' },
    { name: 'Alibaba', color: '#FF6A00', icon: '🟠' },
  ]

  const useCases = [
    {
      icon: Zap,
      title: 'Startups',
      description: 'Keep cloud costs under control as you scale rapidly across multiple regions.',
    },
    {
      icon: Users,
      title: 'Enterprises',
      description: 'Manage hundreds of cloud accounts with centralized visibility and governance.',
    },
    {
      icon: Lock,
      title: 'FinOps Teams',
      description: 'Empower your financial operations with detailed cost allocation and reporting.',
    },
  ]

  return (
    <div className="min-h-screen bg-dark-bg">
      {/* Navigation */}
      <nav className="bg-dark-navy sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <CloudRailLogo size={32} className="text-primary-400" />
              <span className="text-xl font-bold text-white">Cloudrail</span>
            </div>
            <div className="flex items-center gap-8">
              <Link
                to="#solutions"
                className="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              >
                Solutions
              </Link>
              <Link
                to="#platform"
                className="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              >
                Platform
              </Link>
              <Link
                to="/pricing"
                className="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              >
                Pricing
              </Link>
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-gray-300 hover:text-white transition-colors"
              >
                Open Source
              </a>
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  className="px-5 py-2 text-sm font-medium text-white bg-primary-500 rounded hover:bg-primary-600 transition-colors"
                >
                  Dashboard
                </Link>
              ) : (
                <Link
                  to="/register"
                  className="px-5 py-2 text-sm font-medium text-white bg-primary-500 rounded hover:bg-primary-600 transition-colors"
                >
                  Request Demo
                </Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h1 className="text-5xl font-bold text-white mb-6 leading-tight">
              Unlock Peak Cloud Efficiency with Open Source FinOps
            </h1>
            <p className="text-lg text-gray-300 mb-8">
              Cloudrail: The transparent, collaborative platform for multicloud cost management
            </p>
            <div className="flex gap-4">
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  className="px-6 py-3 text-base font-medium text-white bg-primary-500 rounded hover:bg-primary-600 transition-colors"
                >
                  Explore Platform
                </Link>
              ) : (
                <Link
                  to="/register"
                  className="px-6 py-3 text-base font-medium text-white bg-primary-500 rounded hover:bg-primary-600 transition-colors"
                >
                  Explore Platform
                </Link>
              )}
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3 text-base font-medium text-gray-300 bg-transparent border border-gray-600 rounded hover:bg-gray-800 transition-colors"
              >
                View on Github
              </a>
            </div>
          </div>

          {/* 3D Illustration Placeholder */}
          <div className="flex justify-center items-center">
            <div className="relative w-full h-96 flex items-center justify-center">
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="relative">
                  {/* Cloud icons */}
                  <Cloud className="absolute -top-20 -left-10 h-16 w-16 text-primary-400 opacity-80" />
                  <Cloud className="absolute -top-16 right-0 h-20 w-20 text-primary-500 opacity-90" />
                  <Cloud className="absolute -top-12 right-20 h-14 w-14 text-primary-400 opacity-70" />

                  {/* Dashboard mockup */}
                  <div className="bg-gradient-to-br from-primary-500/20 to-primary-700/20 border-2 border-primary-500/50 rounded-lg p-6 w-80 h-52 shadow-2xl transform rotate-3">
                    <div className="space-y-3">
                      <div className="flex gap-2">
                        <div className="h-2 w-2 rounded-full bg-red-400"></div>
                        <div className="h-2 w-2 rounded-full bg-yellow-400"></div>
                        <div className="h-2 w-2 rounded-full bg-green-400"></div>
                      </div>
                      <div className="space-y-2">
                        <div className="h-3 bg-primary-400/30 rounded w-3/4"></div>
                        <div className="h-3 bg-primary-400/20 rounded w-full"></div>
                        <div className="h-3 bg-primary-400/20 rounded w-5/6"></div>
                        <div className="grid grid-cols-3 gap-2 mt-4">
                          <div className="h-16 bg-primary-500/30 rounded"></div>
                          <div className="h-16 bg-primary-500/30 rounded"></div>
                          <div className="h-16 bg-primary-500/30 rounded"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Our Advantages Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-white mb-12">
          Our Advantages
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="bg-dark-card border border-gray-700 rounded-lg p-8">
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-gray-700/50 rounded-full">
                <DollarSign className="h-10 w-10 text-primary-400" />
              </div>
            </div>
            <h3 className="text-xl font-semibold text-white mb-3 text-center">
              Transparent Cost Control
            </h3>
            <p className="text-gray-400 text-center text-sm">
              Manage all and value cloud costs.
            </p>
          </div>

          <div className="bg-dark-card border border-gray-700 rounded-lg p-8">
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-gray-700/50 rounded-full">
                <Users className="h-10 w-10 text-primary-400" />
              </div>
            </div>
            <h3 className="text-xl font-semibold text-white mb-3 text-center">
              Collaborative & Community Driven
            </h3>
            <p className="text-gray-400 text-center text-sm">
              Leverage all and multi cloud platform.
            </p>
          </div>

          <div className="bg-dark-card border border-gray-700 rounded-lg p-8">
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-gray-700/50 rounded-full">
                <Shield className="h-10 w-10 text-primary-400" />
              </div>
            </div>
            <h3 className="text-xl font-semibold text-white mb-3 text-center">
              Secure Sure & Scalable SaaS
            </h3>
            <p className="text-gray-400 text-center text-sm">
              Deploy at will data reach cloud solution.
            </p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-4">
            Key Features
          </h2>
          <p className="text-lg text-gray-300">
            Powerful features designed to give you complete control over your cloud spending
          </p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div
                key={index}
                className="bg-dark-card border border-gray-700 rounded-xl p-6 hover:border-primary-500 transition-all"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-gray-700/50 rounded-lg">
                    <Icon className="h-6 w-6 text-primary-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">{feature.title}</h3>
                </div>
                <p className="text-gray-400">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-white mb-4">
            Built for Every Cloud Team
          </h2>
          <p className="text-lg text-gray-300">
            Whether you're a startup or enterprise, CloudRail scales with your needs
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          {useCases.map((useCase, index) => {
            const Icon = useCase.icon
            return (
              <div
                key={index}
                className="bg-dark-card border border-gray-700 rounded-xl p-8 text-center hover:border-primary-500 transition-all"
              >
                <div className="inline-flex items-center justify-center p-3 bg-gray-700/50 rounded-xl mb-4">
                  <Icon className="h-8 w-8 text-primary-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">{useCase.title}</h3>
                <p className="text-gray-400">{useCase.description}</p>
              </div>
            )
          })}
        </div>
      </section>

      {/* Architecture Designer Highlight */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-gradient-to-r from-gray-900 to-gray-800 rounded-2xl p-12 text-white">
          <div className="max-w-3xl mx-auto text-center">
            <Boxes className="h-16 w-16 mx-auto mb-6 text-primary-400" />
            <h2 className="text-3xl font-bold mb-4">
              Design Before You Deploy
            </h2>
            <p className="text-xl text-gray-300 mb-8">
              Our Architecture Designer lets you plan and estimate costs for complex
              multi-region, multi-AZ deployments with 50+ cloud services before committing
              to any infrastructure.
            </p>
            <div className="flex justify-center gap-8 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary-400" />
                <span>Drag-and-drop interface</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary-400" />
                <span>Real-time cost estimates</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-primary-400" />
                <span>Export architectures</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-dark-card border border-gray-700 rounded-2xl p-12 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Optimize Your Multi-Cloud Costs?
          </h2>
          <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
            Join companies saving thousands on their cloud infrastructure.
            Get started in minutes with our easy setup process.
          </p>
          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-8 py-4 text-lg font-medium text-white bg-primary-500 rounded hover:bg-primary-600 transition-colors"
            >
              Go to Dashboard
              <ArrowRight className="h-5 w-5" />
            </Link>
          ) : (
            <Link
              to="/register"
              className="inline-flex items-center gap-2 px-8 py-4 text-lg font-medium text-white bg-primary-500 rounded hover:bg-primary-600 transition-colors"
            >
              Create Your Free Account
              <ArrowRight className="h-5 w-5" />
            </Link>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CloudRailLogo size={24} className="text-primary-400" />
              <span className="text-lg font-bold text-white">Cloudrail</span>
            </div>
            <p className="text-sm text-gray-400">
              &copy; {new Date().getFullYear()} Cloudrail. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
