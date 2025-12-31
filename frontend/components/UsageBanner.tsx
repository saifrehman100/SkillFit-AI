'use client';

import { useState, useEffect } from 'react';
import { Zap, Crown, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { authAPI, UsageResponse } from '@/lib/api/auth';
import { Button } from '@/components/ui/button';

export default function UsageBanner() {
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUsage();
  }, []);

  const loadUsage = async () => {
    try {
      const response = await authAPI.getUsage();
      setUsage(response.data);
    } catch (error) {
      console.error('Failed to load usage:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !usage) return null;

  // Don't show banner for pro users
  if (usage.plan !== 'free') return null;

  const percentageUsed = (usage.matches_used / usage.matches_limit) * 100;
  const isNearLimit = percentageUsed >= 66;
  const isAtLimit = usage.matches_remaining === 0;

  return (
    <div className={`relative overflow-hidden rounded-lg border p-4 mb-6 ${
      isAtLimit
        ? 'bg-red-500/10 border-red-500/20'
        : isNearLimit
        ? 'bg-yellow-500/10 border-yellow-500/20'
        : 'bg-blue-500/10 border-blue-500/20'
    }`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          {isAtLimit ? (
            <AlertCircle className="h-5 w-5 text-red-400 mt-0.5" />
          ) : (
            <Zap className="h-5 w-5 text-blue-400 mt-0.5" />
          )}
          <div className="flex-1">
            <h3 className={`font-semibold mb-1 ${
              isAtLimit ? 'text-red-400' : isNearLimit ? 'text-yellow-400' : 'text-blue-400'
            }`}>
              {isAtLimit ? 'Free Tier Limit Reached' : 'Free Tier Usage'}
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              {isAtLimit ? (
                <>You've used all {usage.matches_limit} free matches. Upgrade to Pro for unlimited matches!</>
              ) : (
                <>You've used {usage.matches_used} of {usage.matches_limit} free matches. {usage.matches_remaining} remaining.</>
              )}
            </p>

            {/* Progress bar */}
            <div className="w-full bg-muted/50 rounded-full h-2 overflow-hidden">
              <div
                className={`h-full transition-all ${
                  isAtLimit ? 'bg-red-500' : isNearLimit ? 'bg-yellow-500' : 'bg-blue-500'
                }`}
                style={{ width: `${Math.min(percentageUsed, 100)}%` }}
              />
            </div>
          </div>
        </div>

        <Link href="/pricing">
          <Button
            size="sm"
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shrink-0"
          >
            <Crown className="h-4 w-4 mr-2" />
            Upgrade to Pro
          </Button>
        </Link>
      </div>
    </div>
  );
}
