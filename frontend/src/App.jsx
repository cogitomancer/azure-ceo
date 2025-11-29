import { useState, useEffect } from 'react';
import { healthAPI, companyAPI } from './services/api';
import CampaignCreator from './components/CampaignCreator';
import CampaignList from './components/CampaignList';
import ConfigurationPanel from './components/ConfigurationPanel';
import ExperimentAnalysis from './components/ExperimentAnalysis';
import ContentValidator from './components/ContentValidator';
import { 
  Sparkles, 
  Settings, 
  List, 
  BarChart3, 
  Shield,
  Activity,
  Building2,
  Package
} from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('create');
  const [healthStatus, setHealthStatus] = useState(null);
  const [companyData, setCompanyData] = useState(null);
  const [config, setConfig] = useState({
    agents: {
      StrategyLead: { model: 'gpt-4o', temperature: 0.7, max_tokens: 2000 },
      DataSegmenter: { model: 'gpt-4-turbo', temperature: 0.3, max_tokens: 1500 },
      ContentCreator: { model: 'gpt-4o', temperature: 0.8, max_tokens: 2000 },
      ComplianceOfficer: { model: 'gpt-4-turbo', temperature: 0.2, max_tokens: 1000 },
      ExperimentRunner: { model: 'gpt-4-turbo', temperature: 0.3, max_tokens: 1500 },
    },
    safety: {
      hate: 2,
      violence: 2,
      sexual: 2,
      self_harm: 2,
    },
    experiment: {
      default_allocation: [33, 33, 34],
      initial_exposure: 5,
      confidence_level: 0.95,
      minimum_sample_size: 1000,
      minimum_duration_days: 7,
    },
  });

  useEffect(() => {
    // Check backend health on mount
    healthAPI.check()
      .then(data => setHealthStatus({ status: 'connected', ...data }))
      .catch(err => setHealthStatus({ status: 'disconnected', error: err.message }));
    
    // Load company data
    companyAPI.getCompany()
      .then(data => setCompanyData(data))
      .catch(err => console.error('Failed to load company data:', err));
  }, []);

  const tabs = [
    { id: 'create', label: 'Create Campaign', icon: Sparkles },
    { id: 'list', label: 'Campaigns', icon: List },
    { id: 'experiments', label: 'Experiments', icon: BarChart3 },
    { id: 'validate', label: 'Content Validator', icon: Shield },
    { id: 'config', label: 'Configuration', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="bg-primary-600 p-2 rounded-lg">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Marketing Agent System</h1>
                <p className="text-xs text-gray-500">Enterprise AI Campaign Automation</p>
              </div>
            </div>
            
            {/* Company & Health Status */}
            <div className="flex items-center space-x-4">
              {/* Company Info */}
              {companyData && (
                <div className="flex items-center space-x-2 px-3 py-1 bg-blue-50 rounded-full text-sm border border-blue-200">
                  <Building2 className="w-4 h-4 text-blue-600" />
                  <span className="font-medium text-blue-700">{companyData.company?.name}</span>
                  <span className="text-blue-500">|</span>
                  <Package className="w-3 h-3 text-blue-500" />
                  <span className="text-blue-600">{companyData.products_count} products</span>
                </div>
              )}
              
              {/* Health Status */}
              {healthStatus && (
                <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                  healthStatus.status === 'connected' 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-red-100 text-red-700'
                }`}>
                  <Activity className={`w-4 h-4 ${
                    healthStatus.status === 'connected' ? 'animate-pulse' : ''
                  }`} />
                  <span>{healthStatus.status === 'connected' ? 'Connected' : 'Disconnected'}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 ${
                    activeTab === tab.id
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'create' && (
          <CampaignCreator config={config} />
        )}
        {activeTab === 'list' && (
          <CampaignList />
        )}
        {activeTab === 'experiments' && (
          <ExperimentAnalysis />
        )}
        {activeTab === 'validate' && (
          <ContentValidator />
        )}
        {activeTab === 'config' && (
          <ConfigurationPanel config={config} onConfigChange={setConfig} />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            Enterprise Marketing Agent System - Ready for Testing
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
