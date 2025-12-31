'use client';

import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/AuthContext';
import { authAPI } from '@/lib/api/auth';
import { toast } from 'sonner';

interface LLMSettings {
  provider: string | null;
}

export default function SettingsPage() {
  const { user } = useAuth();
  const [selectedProvider, setSelectedProvider] = useState<string>('gemini');
  const [savingLLM, setSavingLLM] = useState(false);
  const [loadingLLM, setLoadingLLM] = useState(true);

  useEffect(() => {
    loadLLMSettings();
  }, []);

  const loadLLMSettings = async () => {
    try {
      const response = await authAPI.getLLMSettings();
      if (response.data.provider) {
        setSelectedProvider(response.data.provider);
      }
    } catch (error) {
      console.error('Failed to load LLM settings:', error);
    } finally {
      setLoadingLLM(false);
    }
  };

  const handleSaveLLMSettings = async () => {
    setSavingLLM(true);
    try {
      const payload = {
        provider: selectedProvider,
      };

      await authAPI.updateLLMSettings(payload);
      toast.success('AI provider saved successfully!');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save AI provider');
    } finally {
      setSavingLLM(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-heading font-bold">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your account settings and preferences
        </p>
      </div>

      {/* Profile */}
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Your account information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              value={user?.email || ''}
              disabled
              className="mt-2"
            />
          </div>
          <div>
            <Label>Account Status</Label>
            <div className="mt-2">
              <span className="inline-flex items-center px-3 py-1 rounded-md bg-green-500/10 text-green-500 text-sm">
                Active
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* LLM Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            AI Provider Preference
          </CardTitle>
          <CardDescription>
            Choose your preferred AI provider for resume analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="llm_provider">AI Provider</Label>
            <select
              id="llm_provider"
              className="w-full mt-2 px-3 py-2 border border-input bg-background rounded-md"
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              disabled={loadingLLM}
            >
              <option value="gemini">Google Gemini 2.0 Flash (Fastest & Free - Default)</option>
              <option value="openai">OpenAI GPT-4o (Latest GPT Model)</option>
              <option value="claude">Anthropic Claude Sonnet 4 (Most Capable)</option>
            </select>
            <p className="text-sm text-muted-foreground mt-2">
              We automatically use the latest model for each provider
            </p>
          </div>

          <Button
            variant="default"
            onClick={handleSaveLLMSettings}
            disabled={savingLLM || loadingLLM}
            className="w-full"
          >
            {savingLLM ? 'Saving...' : 'Save AI Provider'}
          </Button>

          <div className="bg-blue-500/10 border border-blue-500/20 p-4 rounded-lg text-sm">
            <p className="font-medium text-blue-400 mb-2">Current Selection:</p>
            <ul className="space-y-1 text-blue-300">
              <li>• Provider: <span className="font-mono">{selectedProvider}</span></li>
              <li>• Model: <span className="font-mono">
                {selectedProvider === 'gemini' && 'Gemini 2.0 Flash'}
                {selectedProvider === 'openai' && 'GPT-4o'}
                {selectedProvider === 'claude' && 'Claude Sonnet 4'}
              </span></li>
            </ul>
          </div>

          <div className="bg-muted/50 p-4 rounded-lg text-sm">
            <p className="font-medium mb-2">How it works:</p>
            <ul className="space-y-1 text-muted-foreground">
              <li>• We manage all AI API keys for you - no setup required</li>
              <li>• Choose your preferred provider based on speed vs quality</li>
              <li>• Gemini 2.0 Flash: Fastest, free tier available</li>
              <li>• GPT-4o: Latest OpenAI model, excellent quality</li>
              <li>• Claude Sonnet 4: Most capable, best reasoning</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Theme */}
      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>
            Customize the look and feel
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div>
            <Label>Theme</Label>
            <div className="mt-2">
              <span className="inline-flex items-center px-3 py-1 rounded-md bg-primary/10 text-primary text-sm">
                Dark Mode (Default)
              </span>
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              Light mode coming soon
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Danger Zone</CardTitle>
          <CardDescription>
            Irreversible actions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="destructive" disabled>
            Delete Account
          </Button>
          <p className="text-sm text-muted-foreground mt-2">
            Contact support to delete your account
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
