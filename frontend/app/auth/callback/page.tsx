'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { authAPI } from '@/lib/api/auth';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function OAuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'error'>('loading');

  useEffect(() => {
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

      try {
        const response = await authAPI.googleAuth(code);

        // Store token and user data
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));

        toast.success('Logged in successfully with Google!');
        router.push('/dashboard');
      } catch (error: any) {
        console.error('OAuth error:', error);
        toast.error(error.response?.data?.detail || 'Authentication failed');
        setStatus('error');
        setTimeout(() => router.push('/login'), 2000);
      }
    };

    handleCallback();
  }, [searchParams, router]);

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
