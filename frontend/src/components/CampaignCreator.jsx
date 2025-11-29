import { useState, useRef, useEffect } from 'react';
import { campaignAPI, companyAPI } from '../services/api';
import { Send, Loader2, Bot, User, CheckCircle, XCircle, ArrowRight, Building2 } from 'lucide-react';

const AGENT_COLORS = {
  StrategyLead: 'bg-blue-100 text-blue-800 border-blue-300',
  DataSegmenter: 'bg-purple-100 text-purple-800 border-purple-300',
  ContentCreator: 'bg-green-100 text-green-800 border-green-300',
  ComplianceOfficer: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  ExperimentRunner: 'bg-orange-100 text-orange-800 border-orange-300',
};

const WORKFLOW_STAGES = [
  { agent: 'StrategyLead', label: 'Strategy', icon: '🎯' },
  { agent: 'DataSegmenter', label: 'Segmentation', icon: '📊' },
  { agent: 'ContentCreator', label: 'Content', icon: '✍️' },
  { agent: 'ComplianceOfficer', label: 'Compliance', icon: '✅' },
  { agent: 'ExperimentRunner', label: 'Experiment', icon: '🧪' },
];

export default function CampaignCreator({ config }) {
  const [campaignName, setCampaignName] = useState('');
  const [objective, setObjective] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [messages, setMessages] = useState([]);
  const [campaignResult, setCampaignResult] = useState(null);
  const [campaignData, setCampaignData] = useState(null);
  const [error, setError] = useState(null);
  const [currentAgent, setCurrentAgent] = useState(null);
  const [completedAgents, setCompletedAgents] = useState([]);
  const [companyInfo, setCompanyInfo] = useState(null);
  const messagesEndRef = useRef(null);
  const streamControllerRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load company info on mount
    companyAPI.getCompany()
      .then(data => setCompanyInfo(data))
      .catch(err => console.error('Failed to load company:', err));
  }, []);

  const handleCreateCampaign = async () => {
    if (!campaignName.trim() || !objective.trim()) {
      setError('Please provide both campaign name and objective');
      return;
    }

    setError(null);
    setIsStreaming(true);
    setMessages([]);
    setCampaignResult(null);
    setCurrentAgent(null);
    setCompletedAgents([]);

    const campaignData = {
      name: campaignName,
      objective: objective,
      created_by: 'frontend_user',
    };

    try {
      // Use streaming endpoint
      campaignAPI.createCampaignStream(
        campaignData,
        (message) => {
          if (message.event === 'started') {
            setMessages(prev => [...prev, {
              id: Date.now(),
              type: 'system',
              content: `🚀 Campaign "${message.campaign}" started for ${message.company || companyInfo?.company?.name || 'company'}`,
              timestamp: new Date(),
            }]);
          } else if (message.agent_name) {
            // Track workflow progress
            setCurrentAgent(message.agent_name);
            setCompletedAgents(prev => {
              if (!prev.includes(message.agent_name)) {
                return [...prev, message.agent_name];
              }
              return prev;
            });
            
            setMessages(prev => [...prev, {
              id: message.message_id || Date.now(),
              type: 'agent',
              agentName: message.agent_name,
              agentRole: message.agent_role,
              content: message.content,
              timestamp: message.timestamp ? new Date(message.timestamp) : new Date(),
            }]);
          }
        },
        (err) => {
          console.error('Stream error:', err);
          setError(err.message || 'An error occurred during campaign creation');
          setIsStreaming(false);
        },
        (data) => {
          setIsStreaming(false);
          setCurrentAgent(null);
          if (data && data.campaign) {
            // Store full campaign data
            setCampaignData(data.campaign);
            setCampaignResult({
              success: true,
              totalMessages: data.campaign.total_messages || messages.length,
              campaign: data.campaign,
            });
            // Add completion message
            setMessages(prev => [...prev, {
              id: Date.now(),
              type: 'system',
              content: `✅ Campaign "${data.campaign.campaign_name || campaignName}" completed successfully!\n\nTotal messages: ${data.campaign.total_messages || messages.length}\nAgents involved: ${data.campaign.agents_involved?.join(', ') || 'All agents'}`,
              timestamp: new Date(),
            }]);
          } else if (data) {
            // Legacy format with just total_messages
            setCampaignResult({
              success: true,
              totalMessages: data.total_messages || messages.length,
            });
            setMessages(prev => [...prev, {
              id: Date.now(),
              type: 'system',
              content: `✅ Campaign completed successfully! Total messages: ${data.total_messages || messages.length}`,
              timestamp: new Date(),
            }]);
          } else {
            // Stream ended without data
            setMessages(prev => [...prev, {
              id: Date.now(),
              type: 'system',
              content: '✅ Campaign stream completed.',
              timestamp: new Date(),
            }]);
          }
        }
      );
    } catch (err) {
      console.error('Campaign creation error:', err);
      setError(err.message || 'Failed to create campaign');
      setIsStreaming(false);
    }
  };

  const handleStop = () => {
    if (streamControllerRef.current) {
      streamControllerRef.current.abort();
    }
    setIsStreaming(false);
  };

  const handleClear = () => {
    setMessages([]);
    setCampaignResult(null);
    setError(null);
    setCampaignName('');
    setObjective('');
    setCurrentAgent(null);
    setCompletedAgents([]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Create New Campaign</h1>
              <p className="text-gray-600 text-lg">
                Enter your campaign details and watch the AI agents collaborate in real-time
              </p>
            </div>
            {companyInfo && (
              <div className="flex items-center space-x-3 px-5 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200 shadow-sm">
                <Building2 className="w-6 h-6 text-blue-600" />
                <div>
                  <p className="font-semibold text-blue-900">{companyInfo.company?.name}</p>
                  <p className="text-sm text-blue-700">{companyInfo.products_count} products available</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Workflow Progress */}
        {isStreaming && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
            <h3 className="text-lg font-bold text-gray-900 mb-6">Workflow Progress</h3>
            <div className="flex items-center justify-between flex-wrap gap-4">
              {WORKFLOW_STAGES.map((stage, index) => {
                const isCompleted = completedAgents.includes(stage.agent);
                const isCurrent = currentAgent === stage.agent;
                
                return (
                  <div key={stage.agent} className="flex items-center flex-1 min-w-0">
                    <div className={`flex flex-col items-center flex-1 ${
                      isCurrent ? 'scale-105' : ''
                    } transition-transform duration-300`}>
                      <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-2xl transition-all duration-300 shadow-lg ${
                        isCompleted 
                          ? 'bg-gradient-to-br from-green-500 to-green-600 text-white shadow-green-200' 
                          : isCurrent 
                            ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white animate-pulse ring-4 ring-blue-200 shadow-blue-200' 
                            : 'bg-gray-100 text-gray-400 shadow-gray-100'
                      }`}>
                        {isCompleted ? <CheckCircle className="w-7 h-7" /> : stage.icon}
                      </div>
                      <span className={`text-sm mt-3 font-semibold ${
                        isCompleted ? 'text-green-600' : isCurrent ? 'text-blue-600' : 'text-gray-400'
                      }`}>
                        {stage.label}
                      </span>
                    </div>
                    {index < WORKFLOW_STAGES.length - 1 && (
                      <ArrowRight className={`w-5 h-5 mx-3 flex-shrink-0 ${
                        isCompleted ? 'text-green-400' : 'text-gray-300'
                      }`} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Campaign Form */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Campaign Name
              </label>
              <input
                type="text"
                value={campaignName}
                onChange={(e) => setCampaignName(e.target.value)}
                placeholder="e.g., Welcome Campaign for New Runners"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-400 disabled:bg-gray-50 disabled:cursor-not-allowed"
                disabled={isStreaming}
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-900 mb-2">
                Campaign Objective
              </label>
              <textarea
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
                placeholder="e.g., Create a welcome email campaign to increase conversion by 15% for new runner segment"
                rows="5"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-400 resize-none disabled:bg-gray-50 disabled:cursor-not-allowed"
                disabled={isStreaming}
              />
            </div>

            <div className="flex flex-wrap gap-3 pt-2">
              <button
                onClick={handleCreateCampaign}
                disabled={isStreaming || !campaignName.trim() || !objective.trim()}
                className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-lg"
              >
                {isStreaming ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    <span>Creating Campaign...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5 mr-2" />
                    <span>Create Campaign</span>
                  </>
                )}
              </button>

              {isStreaming && (
                <button
                  onClick={handleStop}
                  className="inline-flex items-center px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 font-semibold rounded-xl hover:border-red-500 hover:text-red-600 transition-all duration-200 shadow-sm hover:shadow-md"
                >
                  <XCircle className="w-5 h-5 mr-2" />
                  <span>Stop</span>
                </button>
              )}

              {messages.length > 0 && !isStreaming && (
                <button
                  onClick={handleClear}
                  className="inline-flex items-center px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 font-semibold rounded-xl hover:border-gray-400 hover:bg-gray-50 transition-all duration-200 shadow-sm hover:shadow-md"
                >
                  Clear
                </button>
              )}
            </div>

            {error && (
              <div className="bg-red-50 border-2 border-red-200 rounded-xl p-5 flex items-start space-x-4">
                <XCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-red-900 text-lg">Error</h3>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Agent Messages Stream */}
        {messages.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white">
              <h3 className="text-xl font-bold text-gray-900 flex items-center space-x-3">
                <Bot className="w-6 h-6 text-blue-600" />
                <span>Agent Collaboration</span>
                {isStreaming && (
                  <span className="text-sm font-normal text-gray-500 flex items-center space-x-2 ml-auto">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                    <span>Streaming...</span>
                  </span>
                )}
              </h3>
            </div>

            <div className="p-6 space-y-4 max-h-[600px] overflow-y-auto bg-gray-50">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`p-5 rounded-xl border-2 shadow-sm transition-all duration-200 ${
                    message.type === 'system'
                      ? 'bg-white border-gray-200'
                      : `${AGENT_COLORS[message.agentName] || 'bg-gray-100 border-gray-300'} border-opacity-50`
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      {message.type === 'agent' ? (
                        <Bot className="w-5 h-5" />
                      ) : (
                        <User className="w-5 h-5" />
                      )}
                      <div>
                        <span className="font-bold text-gray-900">
                          {message.type === 'agent' ? message.agentName : 'System'}
                        </span>
                        {message.agentRole && (
                          <span className="text-xs text-gray-500 ml-2">({message.agentRole})</span>
                        )}
                      </div>
                    </div>
                    <span className="text-xs text-gray-500 font-medium">
                      {message.timestamp?.toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                    {message.content}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}

        {/* Campaign Result */}
        {campaignResult && (
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl shadow-lg border-2 border-green-200 p-8">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-green-900 mb-2">Campaign Created Successfully!</h3>
                <p className="text-base text-green-700 mb-6">
                  Total agent messages: <span className="font-semibold">{campaignResult.totalMessages || messages.length}</span>
                  {campaignData?.agents_involved && (
                    <> • Agents: <span className="font-semibold">{campaignData.agents_involved.join(', ')}</span></>
                  )}
                </p>
                
                {/* Natural Language Summary from LLM */}
                {campaignData && campaignData.summary && (
                  <div className="mt-6 pt-6 border-t-2 border-green-200">
                    <h4 className="text-lg font-bold text-green-900 mb-4">Campaign Summary</h4>
                    <div className="bg-white rounded-xl p-6 border border-green-100 shadow-sm">
                      <p className="text-base text-gray-800 whitespace-pre-wrap leading-relaxed">
                        {campaignData.summary}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

