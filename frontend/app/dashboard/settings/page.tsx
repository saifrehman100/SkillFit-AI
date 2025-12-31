'use client';

import { useState, useEffect } from 'react';
import { Copy, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/contexts/AuthContext';
import { authAPI } from '@/lib/api/auth';
import { toast } from 'sonner';

// Best available models for each provider (as of 2025)
const PROVIDER_MODELS = {
  gemini: [
    { value: 'gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash (Recommended - Fast & Free)', recommended: true },
    { value: 'gemini-2.0-flash-thinking-exp-01-21', label: 'Gemini 2.0 Flash Thinking' },
    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
  ],
  openai: [
    { value: 'gpt-4o', label: 'GPT-4o (Recommended - Latest)', recommended: true },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo (Cheaper)' },
  ],
  claude: [
    { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet (Recommended)', recommended: true },
    { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus (Most Capable)' },
    { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku (Fastest)' },
  ],
  openai_compatible: [
    { value: 'custom', label: 'Custom Model', recommended: true },
  ],
};

interface LLMSettings {
  provider: string | null;
  model: string | null;
  has_custom_keys: boolean;
}

export default function SettingsPage() {
  const { user } = useAuth();
  const [apiKey, setApiKey] = useState(user?.api_key || '');
  const [regenerating, setRegenerating] = useState(false);

  // LLM Settings State
  const [llmSettings, setLlmSettings] = useState<LLMSettings>({
    provider: null,
    model: null,
    has_custom_keys: false,
  });
  const [selectedProvider, setSelectedProvider] = useState<string>('gemini');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [apiKeys, setApiKeys] = useState({
    openai: '',
    claude: '',
    gemini: '',
  });
  const [savingLLM, setSavingLLM] = useState(false);
  const [loadingLLM, setLoadingLLM] = useState(true);

  // Load LLM settings on mount
  useEffect(() => {
    loadLLMSettings();
  }, []);

  // Update selected model when provider changes
  useEffect(() => {
    if (selectedProvider && PROVIDER_MODELS[selectedProvider as keyof typeof PROVIDER_MODELS]) {
      const models = PROVIDER_MODELS[selectedProvider as keyof typeof PROVIDER_MODELS];
      const recommended = models.find(m => m.recommended);
      if (!selectedModel && recommended) {
        setSelectedModel(recommended.value);
      }
    }
  }, [selectedProvider]);

  const loadLLMSettings = async () => {
    try {
      const response = await authAPI.getLLMSettings();
      setLlmSettings(response.data);
      if (response.data.provider) {
        setSelectedProvider(response.data.provider);
      }
      if (response.data.model) {
        setSelectedModel(response.data.model);
      }
    } catch (error) {
      console.error('Failed to load LLM settings:', error);
    } finally {
      setLoadingLLM(false);
    }
  };

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

  const handleSaveLLMSettings = async () => {
    setSavingLLM(true);
    try {
      // Build API keys object (only include non-empty keys)
      const apiKeysToSave: Record<string, string> = {};
      if (apiKeys.openai) apiKeysToSave.openai = apiKeys.openai;
      if (apiKeys.claude) apiKeysToSave.claude = apiKeys.claude;
      if (apiKeys.gemini) apiKeysToSave.gemini = apiKeys.gemini;

      const payload = {
        provider: selectedProvider,
        model: selectedModel || undefined,
        api_keys: Object.keys(apiKeysToSave).length > 0 ? apiKeysToSave : undefined,
      };

      const response = await authAPI.updateLLMSettings(payload);
      setLlmSettings(response.data);
      toast.success('LLM settings saved successfully!');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save LLM settings');
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
          <CardTitle>AI Model Preferences</CardTitle>
          <CardDescription>
            Choose your preferred AI provider and model for resume analysis
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
              <option value="gemini">Google Gemini (Fastest & Free)</option>
              <option value="openai">OpenAI (GPT-4)</option>
              <option value="claude">Anthropic (Claude)</option>
              <option value="openai_compatible">Custom OpenAI-Compatible API</option>
            </select>
          </div>

          <div>
            <Label htmlFor="llm_model">Model (Optional)</Label>
            <select
              id="llm_model"
              className="w-full mt-2 px-3 py-2 border border-input bg-background rounded-md"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={loadingLLM}
            >
              <option value="">Use system default</option>
              {PROVIDER_MODELS[selectedProvider as keyof typeof PROVIDER_MODELS]?.map((model) => (
                <option key={model.value} value={model.value}>
                  {model.label}
                </option>
              ))}
            </select>
            <p className="text-sm text-muted-foreground mt-2">
              Leave as &quot;Use system default&quot; to use the best available model for the provider
            </p>
          </div>

          <div className="bg-blue-500/10 border border-blue-500/20 p-4 rounded-lg text-sm">
            <p className="font-medium text-blue-400 mb-2">Current Selection:</p>
            <ul className="space-y-1 text-blue-300">
              <li>• Provider: <span className="font-mono">{selectedProvider}</span></li>
              <li>• Model: <span className="font-mono">{selectedModel || 'System Default'}</span></li>
              {llmSettings.has_custom_keys && (
                <li>• Using your own API keys</li>
              )}
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* User's Own LLM API Keys */}
      <Card>
        <CardHeader>
          <CardTitle>Your AI API Keys (Optional)</CardTitle>
          <CardDescription>
            Add your own API keys to use your AI accounts instead of system defaults
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
              value={apiKeys.openai}
              onChange={(e) => setApiKeys({ ...apiKeys, openai: e.target.value })}
            />
          </div>
          <div>
            <Label htmlFor="anthropic_key">Anthropic (Claude) API Key</Label>
            <Input
              id="anthropic_key"
              type="password"
              placeholder="sk-ant-..."
              className="mt-2 font-mono text-sm"
              value={apiKeys.claude}
              onChange={(e) => setApiKeys({ ...apiKeys, claude: e.target.value })}
            />
          </div>
          <div>
            <Label htmlFor="google_key">Google (Gemini) API Key</Label>
            <Input
              id="google_key"
              type="password"
              placeholder="AIza..."
              className="mt-2 font-mono text-sm"
              value={apiKeys.gemini}
              onChange={(e) => setApiKeys({ ...apiKeys, gemini: e.target.value })}
            />
          </div>

          <Button
            variant="default"
            onClick={handleSaveLLMSettings}
            disabled={savingLLM || loadingLLM}
          >
            {savingLLM ? 'Saving...' : 'Save AI Settings'}
          </Button>

          <div className="bg-muted/50 p-4 rounded-lg text-sm">
            <p className="font-medium mb-2">Note:</p>
            <ul className="space-y-1 text-muted-foreground">
              <li>• Your API keys are stored securely in the database</li>
              <li>• Leave blank to use system defaults (Gemini with our API key)</li>
              <li>• You&apos;ll be charged by the provider when using your own keys</li>
              <li>• Provider selection and model choice are saved separately</li>
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
