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

export default function Landing() {
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
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <CloudRailLogo size={32} className="text-primary-600" />
              <span className="text-2xl font-bold text-gray-900">CloudRail</span>
            </div>
            <div className="flex items-center gap-4">
              <Link
                to="/pricing"
                className="text-sm font-medium text-gray-700 hover:text-primary-600"
              >
                Pricing
              </Link>
              <Link
                to="/login"
                className="text-sm font-medium text-gray-700 hover:text-primary-600"
              >
                Sign in
              </Link>
              <Link
                to="/register"
                className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center max-w-3xl mx-auto">
          <div className="flex justify-center mb-6">
            <CloudRailLogo size={80} className="text-primary-600" />
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Multi-Cloud Cost Management
            <span className="text-primary-600"> Simplified</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            CloudRail helps you monitor, analyze, and optimize costs across AWS, GCP, Azure,
            and Alibaba Cloud with powerful analytics, intelligent recommendations, and real-time alerts.
          </p>
          <div className="flex justify-center gap-4 mb-12">
            <Link
              to="/register"
              className="inline-flex items-center gap-2 px-6 py-3 text-base font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
            >
              Start Free Trial
              <ArrowRight className="h-5 w-5" />
            </Link>
            <a
              href="#features"
              className="inline-flex items-center gap-2 px-6 py-3 text-base font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Learn More
            </a>
          </div>

          {/* Cloud Provider Logos */}
          <div className="flex justify-center items-center gap-6 pt-8 border-t">
            <span className="text-sm text-gray-500 font-medium">Supported Platforms:</span>
            {cloudProviders.map((provider) => (
              <div key={provider.name} className="flex items-center gap-2">
                <span className="text-2xl">{provider.icon}</span>
                <span className="text-sm font-medium text-gray-700">{provider.name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-primary-50 rounded-2xl p-8 md:p-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            Why Choose CloudRail?
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {benefits.map((benefit, index) => (
              <div key={index} className="flex items-start gap-3">
                <CheckCircle className="h-6 w-6 text-primary-600 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700">{benefit}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Everything You Need for Multi-Cloud Cost Management
          </h2>
          <p className="text-lg text-gray-600">
            Powerful features designed to give you complete control over your cloud spending
          </p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div
                key={index}
                className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-primary-100 rounded-lg">
                    <Icon className="h-6 w-6 text-primary-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">{feature.title}</h3>
                </div>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Built for Every Cloud Team
          </h2>
          <p className="text-lg text-gray-600">
            Whether you're a startup or enterprise, CloudRail scales with your needs
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          {useCases.map((useCase, index) => {
            const Icon = useCase.icon
            return (
              <div
                key={index}
                className="bg-gradient-to-br from-primary-50 to-white border border-primary-100 rounded-xl p-8 text-center"
              >
                <div className="inline-flex items-center justify-center p-3 bg-primary-100 rounded-xl mb-4">
                  <Icon className="h-8 w-8 text-primary-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">{useCase.title}</h3>
                <p className="text-gray-600">{useCase.description}</p>
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
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-2xl p-12 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Optimize Your Multi-Cloud Costs?
          </h2>
          <p className="text-xl text-primary-100 mb-8 max-w-2xl mx-auto">
            Join companies saving thousands on their cloud infrastructure.
            Get started in minutes with our easy setup process.
          </p>
          <Link
            to="/register"
            className="inline-flex items-center gap-2 px-8 py-4 text-lg font-medium text-primary-600 bg-white rounded-lg hover:bg-gray-50 transition-colors"
          >
            Create Your Free Account
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-gray-50 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CloudRailLogo size={24} className="text-primary-600" />
              <span className="text-lg font-bold text-gray-900">CloudRail</span>
            </div>
            <p className="text-sm text-gray-600">
              &copy; {new Date().getFullYear()} CloudRail. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
