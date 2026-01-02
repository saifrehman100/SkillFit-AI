'use client';

import { useEffect, useState, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { authAPI } from '@/lib/api/auth';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

function OAuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshUser } = useAuth();
  const [status, setStatus] = useState<'loading' | 'error'>('loading');
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Prevent multiple calls (React StrictMode runs effects twice in dev)
    if (hasProcessed.current) {
      return;
    }

    const handleCallback = async () => {
      const code = searchParams.get('code');
      const error = searchParams.get('error');

      if (error) {
        toast.error('OAuth authentication failed');
        setStatus('error');
        setTimeout(() => router.push('/login'), 2000);
        return;
      }

      if (!code) {
        toast.error('No authorization code received');
        setStatus('error');
        setTimeout(() => router.push('/login'), 2000);
        return;
      }

      // Mark as processed before making the API call
      hasProcessed.current = true;

      try {
        const response = await authAPI.googleAuth(code);

        // Store token
        localStorage.setItem('access_token', response.data.access_token);

        // Refresh user in AuthContext to update state
        await refreshUser();

        toast.success('Logged in successfully with Google!');
        router.push('/dashboard');
      } catch (error: any) {
        console.error('OAuth error:', error);
        toast.error(error.response?.data?.detail || 'Authentication failed');
        setStatus('error');
        hasProcessed.current = false; // Reset on error so user can retry
        setTimeout(() => router.push('/login'), 2000);
      }
    };

    handleCallback();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center space-y-4">
        {status === 'loading' ? (
          <>
            <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
            <p className="text-muted-foreground">Completing Google sign-in...</p>
          </>
        ) : (
          <>
            <p className="text-destructive">Authentication failed. Redirecting...</p>
          </>
        )}
      </div>
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary mb-4" />
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    }>
      <OAuthCallbackContent />
    </Suspense>
  );
}
