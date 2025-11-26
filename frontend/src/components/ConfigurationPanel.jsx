import { useState } from 'react';
import { Save, RotateCcw } from 'lucide-react';

const AGENT_NAMES = [
  'StrategyLead',
  'DataSegmenter',
  'ContentCreator',
  'ComplianceOfficer',
  'ExperimentRunner',
];

const MODEL_OPTIONS = ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'];

export default function ConfigurationPanel({ config, onConfigChange }) {
  const [localConfig, setLocalConfig] = useState(config);
  const [activeSection, setActiveSection] = useState('agents');
  const [saved, setSaved] = useState(false);

  const updateAgentConfig = (agentName, field, value) => {
    setLocalConfig(prev => ({
      ...prev,
      agents: {
        ...prev.agents,
        [agentName]: {
          ...prev.agents[agentName],
          [field]: field === 'temperature' || field === 'max_tokens' 
            ? parseFloat(value) || 0 
            : value,
        },
      },
    }));
    setSaved(false);
  };

  const updateSafetyConfig = (field, value) => {
    setLocalConfig(prev => ({
      ...prev,
      safety: {
        ...prev.safety,
        [field]: parseInt(value) || 0,
      },
    }));
    setSaved(false);
  };

  const updateExperimentConfig = (field, value) => {
    setLocalConfig(prev => ({
      ...prev,
      experiment: {
        ...prev.experiment,
        [field]: field === 'confidence_level'
          ? parseFloat(value) || 0
          : field === 'default_allocation'
          ? value.split(',').map(v => parseInt(v.trim()) || 0)
          : parseInt(value) || 0,
      },
    }));
    setSaved(false);
  };

  const handleSave = () => {
    onConfigChange(localConfig);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleReset = () => {
    setLocalConfig(config);
    setSaved(false);
  };

  const sections = [
    { id: 'agents', label: 'Agent Settings' },
    { id: 'safety', label: 'Safety Thresholds' },
    { id: 'experiment', label: 'Experiment Settings' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Configuration</h2>
            <p className="text-gray-600">
              Adjust agent parameters, safety thresholds, and experiment settings
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={handleReset}
              className="btn-secondary flex items-center space-x-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset</span>
            </button>
            <button
              onClick={handleSave}
              className="btn-primary flex items-center space-x-2"
            >
              <Save className="w-4 h-4" />
              <span>Save Changes</span>
            </button>
          </div>
        </div>
        {saved && (
          <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-700">
            Configuration saved successfully!
          </div>
        )}
      </div>

      {/* Section Tabs */}
      <div className="card">
        <div className="flex space-x-1 border-b border-gray-200">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                activeSection === section.id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {section.label}
            </button>
          ))}
        </div>
      </div>

      {/* Agent Settings */}
      {activeSection === 'agents' && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Configuration</h3>
          <div className="space-y-6">
            {AGENT_NAMES.map((agentName) => (
              <div
                key={agentName}
                className="border border-gray-200 rounded-lg p-4"
              >
                <h4 className="font-semibold text-gray-900 mb-4">{agentName}</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="label">Model</label>
                    <select
                      value={localConfig.agents[agentName]?.model || 'gpt-4o'}
                      onChange={(e) => updateAgentConfig(agentName, 'model', e.target.value)}
                      className="input-field"
                    >
                      {MODEL_OPTIONS.map((model) => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label">
                      Temperature: {localConfig.agents[agentName]?.temperature || 0.7}
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={localConfig.agents[agentName]?.temperature || 0.7}
                      onChange={(e) =>
                        updateAgentConfig(agentName, 'temperature', e.target.value)
                      }
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Conservative (0)</span>
                      <span>Creative (1)</span>
                    </div>
                  </div>
                  <div>
                    <label className="label">Max Tokens</label>
                    <input
                      type="number"
                      min="100"
                      max="4000"
                      step="100"
                      value={localConfig.agents[agentName]?.max_tokens || 2000}
                      onChange={(e) =>
                        updateAgentConfig(agentName, 'max_tokens', e.target.value)
                      }
                      className="input-field"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Safety Settings */}
      {activeSection === 'safety' && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Content Safety Thresholds</h3>
          <p className="text-sm text-gray-600 mb-6">
            Adjust safety thresholds (0-7 scale, lower = stricter)
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.keys(localConfig.safety || {}).map((category) => (
              <div key={category} className="border border-gray-200 rounded-lg p-4">
                <label className="label capitalize">
                  {category.replace('_', ' ')}: {localConfig.safety[category]}
                </label>
                <input
                  type="range"
                  min="0"
                  max="7"
                  step="1"
                  value={localConfig.safety[category] || 2}
                  onChange={(e) => updateSafetyConfig(category, e.target.value)}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Strict (0)</span>
                  <span>Lenient (7)</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Experiment Settings */}
      {activeSection === 'experiment' && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Experiment Configuration</h3>
          <div className="space-y-4">
            <div>
              <label className="label">Default Allocation (%)</label>
              <input
                type="text"
                value={localConfig.experiment?.default_allocation?.join(', ') || '33, 33, 34'}
                onChange={(e) => updateExperimentConfig('default_allocation', e.target.value)}
                placeholder="33, 33, 34"
                className="input-field"
              />
              <p className="text-xs text-gray-500 mt-1">
                Comma-separated percentages for variant allocation
              </p>
            </div>
            <div>
              <label className="label">Initial Exposure (%)</label>
              <input
                type="number"
                min="1"
                max="100"
                value={localConfig.experiment?.initial_exposure || 5}
                onChange={(e) => updateExperimentConfig('initial_exposure', e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label className="label">
                Confidence Level: {localConfig.experiment?.confidence_level || 0.95}
              </label>
              <input
                type="range"
                min="0.8"
                max="0.99"
                step="0.01"
                value={localConfig.experiment?.confidence_level || 0.95}
                onChange={(e) => updateExperimentConfig('confidence_level', e.target.value)}
                className="w-full"
              />
            </div>
            <div>
              <label className="label">Minimum Sample Size</label>
              <input
                type="number"
                min="100"
                step="100"
                value={localConfig.experiment?.minimum_sample_size || 1000}
                onChange={(e) => updateExperimentConfig('minimum_sample_size', e.target.value)}
                className="input-field"
              />
            </div>
            <div>
              <label className="label">Minimum Duration (days)</label>
              <input
                type="number"
                min="1"
                value={localConfig.experiment?.minimum_duration_days || 7}
                onChange={(e) => updateExperimentConfig('minimum_duration_days', e.target.value)}
                className="input-field"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

