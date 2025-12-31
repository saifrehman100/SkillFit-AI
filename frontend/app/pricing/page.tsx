'use client';

import { Check, Crown, Zap } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function PricingPage() {
  const plans = [
    {
      name: 'Free',
      price: '$0',
      description: 'Perfect for trying out SkillFit AI',
      features: [
        '3 AI-powered resume matches',
        'Upload unlimited resumes',
        'Add unlimited job postings',
        'Basic match analysis',
        'Application tracking',
      ],
      limitations: [
        'Limited to 3 matches total',
        'Basic support',
      ],
      cta: 'Current Plan',
      highlighted: false,
      disabled: true,
    },
    {
      name: 'Pro',
      price: '$29',
      period: '/month',
      description: 'For serious job seekers',
      features: [
        'Unlimited AI-powered matches',
        'Upload unlimited resumes',
        'Add unlimited job postings',
        'Detailed match analysis',
        'Missing skills insights',
        'Personalized recommendations',
        'Application tracking',
        'Priority support',
        'Advanced analytics',
        'Export reports',
      ],
      cta: 'Upgrade to Pro',
      highlighted: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      description: 'For teams and recruiters',
      features: [
        'Everything in Pro',
        'Team collaboration',
        'Bulk candidate screening',
        'Custom AI models',
        'API access',
        'Dedicated account manager',
        'Custom integrations',
        'SLA guarantee',
      ],
      cta: 'Contact Sales',
      highlighted: false,
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-heading font-bold">SkillFit AI</h1>
        </div>
      </div>

      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-heading font-bold mb-4">
            Simple, transparent pricing
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Choose the plan that&apos;s right for you. Upgrade or downgrade anytime.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan) => (
            <Card
              key={plan.name}
              className={`relative ${
                plan.highlighted
                  ? 'border-primary shadow-lg scale-105'
                  : 'border-border'
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-1 rounded-full text-sm font-medium inline-flex items-center gap-1">
                    <Crown className="h-4 w-4" />
                    Most Popular
                  </span>
                </div>
              )}

              <CardHeader className="text-center pb-8 pt-8">
                <CardTitle className="text-2xl mb-2">{plan.name}</CardTitle>
                <div className="mb-2">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  {plan.period && (
                    <span className="text-muted-foreground">{plan.period}</span>
                  )}
                </div>
                <CardDescription>{plan.description}</CardDescription>
              </CardHeader>

              <CardContent className="space-y-6">
                <ul className="space-y-3">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <Check className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                  {plan.limitations?.map((limitation, index) => (
                    <li
                      key={`limit-${index}`}
                      className="flex items-start gap-2 text-muted-foreground"
                    >
                      <Check className="h-5 w-5 opacity-30 shrink-0 mt-0.5" />
                      <span className="text-sm">{limitation}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  className={`w-full ${
                    plan.highlighted
                      ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700'
                      : ''
                  }`}
                  variant={plan.highlighted ? 'default' : 'outline'}
                  disabled={plan.disabled}
                >
                  {plan.highlighted && <Zap className="h-4 w-4 mr-2" />}
                  {plan.cta}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* FAQ Section */}
        <div className="mt-24 max-w-3xl mx-auto">
          <h2 className="text-3xl font-heading font-bold text-center mb-12">
            Frequently Asked Questions
          </h2>

          <div className="space-y-6">
            <div>
              <h3 className="font-semibold mb-2">Can I upgrade or downgrade anytime?</h3>
              <p className="text-muted-foreground">
                Yes! You can upgrade to Pro anytime to unlock unlimited matches. If you downgrade, you&apos;ll keep access until the end of your billing period.
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-2">What happens when I reach the free tier limit?</h3>
              <p className="text-muted-foreground">
                You&apos;ll be prompted to upgrade to Pro to create more matches. You can still access your existing matches, upload resumes, and add jobs.
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-2">How does billing work?</h3>
              <p className="text-muted-foreground">
                Pro plan is billed monthly. You can cancel anytime with no long-term contracts. We&apos;ll send you an invoice each month.
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-2">Which AI models do you use?</h3>
              <p className="text-muted-foreground">
                We support multiple AI providers (Gemini, GPT-4, Claude). You can choose your preferred model in Settings. We manage all API keys securely.
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-2">Is my data secure?</h3>
              <p className="text-muted-foreground">
                Yes. All resumes and job descriptions are encrypted at rest and in transit. We never share your data with third parties.
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-24 text-center">
          <div className="bg-gradient-to-r from-purple-600/10 to-pink-600/10 border border-purple-600/20 rounded-lg p-8 max-w-2xl mx-auto">
            <h2 className="text-2xl font-heading font-bold mb-4">
              Ready to supercharge your job search?
            </h2>
            <p className="text-muted-foreground mb-6">
              Join thousands of job seekers using AI to land their dream jobs faster.
            </p>
            <Button
              size="lg"
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
            >
              <Crown className="h-5 w-5 mr-2" />
              Start with Free Tier
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
