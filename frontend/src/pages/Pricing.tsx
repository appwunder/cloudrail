import { useState } from 'react';
import { Check } from 'lucide-react';
import axios from 'axios';

const Pricing = () => {
    const [loading, setLoading] = useState<string | null>(null);

    const handleUpgrade = async (planType: string) => {
        setLoading(planType);
        try {
            // Get token from local storage (assuming auth implementation stores it there)
            const token = localStorage.getItem('token');

            const response = await axios.post(
                '/api/v1/billing/create-checkout-session',
                null,
                {
                    params: { plan_type: planType },
                    headers: { Authorization: `Bearer ${token}` }
                }
            );

            // Redirect to Stripe Checkout
            window.location.href = response.data.url;
        } catch (error) {
            console.error('Error creating checkout session:', error);
            alert('Failed to start checkout session. Please try again.');
        } finally {
            setLoading(null);
        }
    };

    const plans = [
        {
            name: 'Free',
            price: '$0',
            period: '/month',
            description: 'Perfect for trying out CloudCostly',
            features: [
                '1 AWS Account',
                '7-day cost history',
                'Basic dashboard',
                'Community support',
            ],
            cta: 'Current Plan',
            disabled: true,
            type: 'free'
        },
        {
            name: 'Professional',
            price: '$299',
            period: '/month',
            description: 'For growing teams and startups',
            features: [
                '5 AWS Accounts',
                '90-day cost history',
                'Full analytics',
                'Basic recommendations',
                'Email support',
            ],
            cta: 'Upgrade to Pro',
            highlight: true,
            type: 'pro'
        },
        {
            name: 'Business',
            price: '$999',
            period: '/month',
            description: 'For scaling organizations',
            features: [
                '20 AWS Accounts',
                'Unlimited history',
                'Advanced recommendations',
                'Compute Optimizer',
                'Priority support',
            ],
            cta: 'Upgrade to Business',
            type: 'business'
        }
    ];

    return (
        <div className="py-12 px-4 sm:px-6 lg:px-8 bg-gray-50 min-h-screen">
            <div className="max-w-7xl mx-auto">
                <div className="text-center">
                    <h2 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
                        Simple, transparent pricing
                    </h2>
                    <p className="mt-4 text-xl text-gray-600">
                        Choose the plan that fits your cloud infrastructure needs
                    </p>
                </div>

                <div className="mt-12 space-y-4 sm:mt-16 sm:space-y-0 sm:grid sm:grid-cols-2 sm:gap-6 lg:max-w-4xl lg:mx-auto xl:max-w-none xl:mx-0 xl:grid-cols-3">
                    {plans.map((plan) => (
                        <div
                            key={plan.name}
                            className={`border rounded-lg shadow-sm divide-y divide-gray-200 bg-white flex flex-col ${plan.highlight ? 'ring-2 ring-indigo-500 relative' : ''
                                }`}
                        >
                            {plan.highlight && (
                                <div className="absolute top-0 right-0 -mt-4 mr-4 bg-indigo-500 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">
                                    Most Popular
                                </div>
                            )}
                            <div className="p-6">
                                <h3 className="text-lg leading-6 font-medium text-gray-900">{plan.name}</h3>
                                <p className="mt-4 text-sm text-gray-500">{plan.description}</p>
                                <p className="mt-8">
                                    <span className="text-4xl font-extrabold text-gray-900">{plan.price}</span>
                                    <span className="text-base font-medium text-gray-500">{plan.period}</span>
                                </p>
                                <button
                                    onClick={() => !plan.disabled && handleUpgrade(plan.type)}
                                    disabled={plan.disabled || loading === plan.type}
                                    className={`mt-8 block w-full py-3 px-6 border border-transparent rounded-md text-center font-medium ${plan.disabled
                                        ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                                        : 'bg-indigo-600 text-white hover:bg-indigo-700'
                                        }`}
                                >
                                    {loading === plan.type ? 'Processing...' : plan.cta}
                                </button>
                            </div>
                            <div className="pt-6 pb-8 px-6 flex-1">
                                <h4 className="text-sm font-medium text-gray-900 tracking-wide uppercase">What's included</h4>
                                <ul className="mt-6 space-y-4">
                                    {plan.features.map((feature) => (
                                        <li key={feature} className="flex space-x-3">
                                            <Check className="flex-shrink-0 h-5 w-5 text-green-500" aria-hidden="true" />
                                            <span className="text-sm text-gray-500">{feature}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Pricing;
