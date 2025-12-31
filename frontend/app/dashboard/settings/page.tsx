'use client';

import { useState } from 'react';
import { Copy, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/AuthContext';
import { authAPI } from '@/lib/api/auth';
import { toast } from 'sonner';

export default function SettingsPage() {
  const { user } = useAuth();
  const [apiKey, setApiKey] = useState(user?.api_key || '');
  const [regenerating, setRegenerating] = useState(false);

  const handleCopyApiKey = () => {
    navigator.clipboard.writeText(apiKey);
    toast.success('API key copied to clipboard');
  };

  const handleRegenerateApiKey = async () => {
    if (!confirm('Are you sure? This will invalidate your current API key.')) return;

    setRegenerating(true);
    try {
      const response = await authAPI.regenerateAPIKey();
      setApiKey(response.data.api_key);
      toast.success('API key regenerated successfully');
    } catch (error) {
      toast.error('Failed to regenerate API key');
    } finally {
      setRegenerating(false);
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

      {/* API Key */}
      <Card>
        <CardHeader>
          <CardTitle>API Key</CardTitle>
          <CardDescription>
            Use this key to authenticate API requests
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="apiKey">Your API Key</Label>
            <div className="flex gap-2 mt-2">
              <Input
                id="apiKey"
                value={apiKey}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={handleCopyApiKey}
                title="Copy API key"
              >
                <Copy className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={handleRegenerateApiKey}
                disabled={regenerating}
                title="Regenerate API key"
              >
                <RefreshCw className={`h-4 w-4 ${regenerating ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
          <div className="bg-muted/50 p-4 rounded-lg text-sm">
            <p className="font-medium mb-2">Important:</p>
            <ul className="space-y-1 text-muted-foreground">
              <li>• Keep your API key secret</li>
              <li>• Regenerating will invalidate the old key</li>
              <li>• Use the X-API-Key header in requests</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* LLM Preferences */}
      <Card>
        <CardHeader>
          <CardTitle>LLM Preferences</CardTitle>
          <CardDescription>
            Default AI model settings for analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="llm_provider">Default Provider</Label>
            <select
              id="llm_provider"
              className="w-full mt-2 px-3 py-2 border border-input bg-background rounded-md"
              defaultValue="gemini"
            >
              <option value="gemini">Google Gemini (Default)</option>
              <option value="openai">OpenAI (GPT-4)</option>
              <option value="claude">Anthropic (Claude)</option>
            </select>
          </div>
          <p className="text-sm text-muted-foreground">
            Note: You can override this setting when creating matches. System uses Gemini by default.
          </p>
        </CardContent>
      </Card>

      {/* User's Own LLM API Keys */}
      <Card>
        <CardHeader>
          <CardTitle>Your LLM API Keys (Optional)</CardTitle>
          <CardDescription>
            Add your own API keys to use your LLM accounts instead of the system defaults
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="openai_key">OpenAI API Key</Label>
            <Input
              id="openai_key"
              type="password"
              placeholder="sk-..."
              className="mt-2 font-mono text-sm"
            />
          </div>
          <div>
            <Label htmlFor="anthropic_key">Anthropic (Claude) API Key</Label>
            <Input
              id="anthropic_key"
              type="password"
              placeholder="sk-ant-..."
              className="mt-2 font-mono text-sm"
            />
          </div>
          <div>
            <Label htmlFor="google_key">Google (Gemini) API Key</Label>
            <Input
              id="google_key"
              type="password"
              placeholder="AIza..."
              className="mt-2 font-mono text-sm"
            />
          </div>
          <Button variant="default" disabled>
            Save API Keys
          </Button>
          <div className="bg-muted/50 p-4 rounded-lg text-sm">
            <p className="font-medium mb-2">Note:</p>
            <ul className="space-y-1 text-muted-foreground">
              <li>• Your API keys are encrypted and stored securely</li>
              <li>• Leave blank to use system defaults (Gemini)</li>
              <li>• You&apos;ll be charged by the provider when using your own keys</li>
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
