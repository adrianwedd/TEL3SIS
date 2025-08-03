import React, { useEffect, useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

interface AgentConfig {
  prompt: string;
  voice: string;
  temperature?: number;
  max_tokens?: number;
  tools_enabled?: string[];
  escalation_triggers?: string[];
}

const Settings: React.FC = () => {
  const [config, setConfig] = useState<AgentConfig>({
    prompt: '',
    voice: '',
    temperature: 0.7,
    max_tokens: 150,
    tools_enabled: [],
    escalation_triggers: [],
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [saved, setSaved] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const token = localStorage.getItem('token');

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }

    const fetchConfig = async () => {
      try {
        setLoading(true);
        const response = await fetch('/v1/admin/config', {
          headers: { 'X-API-Key': token },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch config: ${response.status}`);
        }

        const data: AgentConfig = await response.json();
        setConfig({
          prompt: data.prompt || '',
          voice: data.voice || '',
          temperature: data.temperature ?? 0.7,
          max_tokens: data.max_tokens ?? 150,
          tools_enabled: data.tools_enabled || [],
          escalation_triggers: data.escalation_triggers || [],
        });
        setError(null);
      } catch (err) {
        console.error('Failed to fetch config:', err);
        setError(err instanceof Error ? err.message : 'Failed to load configuration');
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();
  }, [token, navigate]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!token) return;

    setSaving(true);
    setError(null);

    try {
      const response = await fetch('/v1/admin/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': token,
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`Failed to save config: ${response.status}`);
      }

      setSaved(true);
      setTimeout(() => {
        setSaved(false);
      }, 3000);
    } catch (err) {
      console.error('Failed to save config:', err);
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleConfigChange = (field: keyof AgentConfig, value: any) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  const availableTools = [
    'calendar',
    'weather',
    'notifications',
    'translation',
    'sentiment'
  ];

  const handleToolToggle = (tool: string) => {
    const currentTools = config.tools_enabled || [];
    const newTools = currentTools.includes(tool)
      ? currentTools.filter(t => t !== tool)
      : [...currentTools, tool];
    
    handleConfigChange('tools_enabled', newTools);
  };

  if (loading) {
    return (
      <div className="settings">
        <div className="loading">Loading configuration...</div>
      </div>
    );
  }

  return (
    <div className="settings">
      <div className="settings-header">
        <h2>Agent Configuration</h2>
        <button 
          onClick={() => navigate('/dashboard')}
          className="btn-secondary"
        >
          Back to Dashboard
        </button>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="settings-form">
        <div className="form-section">
          <h3>Agent Behavior</h3>
          
          <div className="form-group">
            <label htmlFor="prompt">System Prompt</label>
            <textarea
              id="prompt"
              value={config.prompt}
              onChange={(e) => handleConfigChange('prompt', e.target.value)}
              placeholder="Enter the system prompt for the agent..."
              rows={6}
              required
            />
            <small>This defines the agent's personality and behavior instructions.</small>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="temperature">Temperature</label>
              <input
                id="temperature"
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={config.temperature}
                onChange={(e) => handleConfigChange('temperature', parseFloat(e.target.value))}
              />
              <small>Controls randomness (0.0 = deterministic, 1.0 = creative)</small>
            </div>

            <div className="form-group">
              <label htmlFor="max_tokens">Max Tokens</label>
              <input
                id="max_tokens"
                type="number"
                min="50"
                max="500"
                value={config.max_tokens}
                onChange={(e) => handleConfigChange('max_tokens', parseInt(e.target.value))}
              />
              <small>Maximum response length</small>
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Voice Configuration</h3>
          
          <div className="form-group">
            <label htmlFor="voice">Voice ID</label>
            <input
              id="voice"
              type="text"
              value={config.voice}
              onChange={(e) => handleConfigChange('voice', e.target.value)}
              placeholder="ElevenLabs voice ID"
              required
            />
            <small>ElevenLabs voice identifier for text-to-speech</small>
          </div>
        </div>

        <div className="form-section">
          <h3>Available Tools</h3>
          <div className="tools-grid">
            {availableTools.map(tool => (
              <label key={tool} className="tool-checkbox">
                <input
                  type="checkbox"
                  checked={config.tools_enabled?.includes(tool) || false}
                  onChange={() => handleToolToggle(tool)}
                />
                <span className="tool-name">{tool}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="form-section">
          <h3>Escalation Triggers</h3>
          <div className="form-group">
            <label htmlFor="escalation_triggers">Keywords for Human Handoff</label>
            <input
              id="escalation_triggers"
              type="text"
              value={config.escalation_triggers?.join(', ') || ''}
              onChange={(e) => handleConfigChange('escalation_triggers', 
                e.target.value.split(',').map(s => s.trim()).filter(Boolean)
              )}
              placeholder="urgent, emergency, manager, supervisor"
            />
            <small>Comma-separated keywords that trigger human escalation</small>
          </div>
        </div>

        <div className="form-actions">
          <button 
            type="submit" 
            className="btn-primary"
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
          
          {saved && (
            <div className="success-message">
              Configuration saved successfully!
            </div>
          )}
        </div>
      </form>
    </div>
  );
};

export default Settings;