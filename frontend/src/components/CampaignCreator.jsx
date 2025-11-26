import { useState, useRef, useEffect } from 'react';
import { campaignAPI } from '../services/api';
import { Send, Loader2, Bot, User, CheckCircle, XCircle } from 'lucide-react';

const AGENT_COLORS = {
  StrategyLead: 'bg-blue-100 text-blue-800 border-blue-300',
  DataSegmenter: 'bg-purple-100 text-purple-800 border-purple-300',
  ContentCreator: 'bg-green-100 text-green-800 border-green-300',
  ComplianceOfficer: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  ExperimentRunner: 'bg-orange-100 text-orange-800 border-orange-300',
};

export default function CampaignCreator({ config }) {
  const [campaignName, setCampaignName] = useState('');
  const [objective, setObjective] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [messages, setMessages] = useState([]);
  const [campaignResult, setCampaignResult] = useState(null);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const streamControllerRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleCreateCampaign = async () => {
    if (!campaignName.trim() || !objective.trim()) {
      setError('Please provide both campaign name and objective');
      return;
    }

    setError(null);
    setIsStreaming(true);
    setMessages([]);
    setCampaignResult(null);

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
              content: `Campaign "${message.campaign}" started`,
              timestamp: new Date(),
            }]);
          } else if (message.agent_name) {
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
          if (data) {
            setCampaignResult({
              success: true,
              totalMessages: data.total_messages,
            });
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
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Create New Campaign</h2>
        <p className="text-gray-600">
          Enter your campaign details and watch the AI agents collaborate in real-time
        </p>
      </div>

      {/* Campaign Form */}
      <div className="card">
        <div className="space-y-4">
          <div>
            <label className="label">Campaign Name</label>
            <input
              type="text"
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
              placeholder="e.g., Welcome Campaign for New Runners"
              className="input-field"
              disabled={isStreaming}
            />
          </div>

          <div>
            <label className="label">Campaign Objective</label>
            <textarea
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              placeholder="e.g., Create a welcome email campaign to increase conversion by 15% for new runner segment"
              rows="4"
              className="input-field"
              disabled={isStreaming}
            />
          </div>

          <div className="flex space-x-3">
            <button
              onClick={handleCreateCampaign}
              disabled={isStreaming || !campaignName.trim() || !objective.trim()}
              className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isStreaming ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Creating Campaign...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Create Campaign</span>
                </>
              )}
            </button>

            {isStreaming && (
              <button
                onClick={handleStop}
                className="btn-secondary flex items-center space-x-2"
              >
                <XCircle className="w-4 h-4" />
                <span>Stop</span>
              </button>
            )}

            {messages.length > 0 && !isStreaming && (
              <button
                onClick={handleClear}
                className="btn-secondary"
              >
                Clear
              </button>
            )}
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
              <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-900">Error</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Agent Messages Stream */}
      {messages.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
            <Bot className="w-5 h-5" />
            <span>Agent Collaboration</span>
            {isStreaming && (
              <span className="text-sm font-normal text-gray-500 flex items-center space-x-1">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Streaming...</span>
              </span>
            )}
          </h3>

          <div className="space-y-4 max-h-[600px] overflow-y-auto">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`p-4 rounded-lg border ${
                  message.type === 'system'
                    ? 'bg-gray-50 border-gray-200'
                    : AGENT_COLORS[message.agentName] || 'bg-gray-100 border-gray-300'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {message.type === 'agent' ? (
                      <Bot className="w-4 h-4" />
                    ) : (
                      <User className="w-4 h-4" />
                    )}
                    <span className="font-semibold">
                      {message.type === 'agent' ? message.agentName : 'System'}
                    </span>
                    {message.agentRole && (
                      <span className="text-xs opacity-75">({message.agentRole})</span>
                    )}
                  </div>
                  <span className="text-xs opacity-75">
                    {message.timestamp?.toLocaleTimeString()}
                  </span>
                </div>
                <div className="text-sm whitespace-pre-wrap">{message.content}</div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      {/* Campaign Result */}
      {campaignResult && (
        <div className="card bg-green-50 border-green-200">
          <div className="flex items-start space-x-3">
            <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-green-900">Campaign Created Successfully!</h3>
              <p className="text-sm text-green-700 mt-1">
                Total agent messages: {campaignResult.totalMessages || messages.length}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

