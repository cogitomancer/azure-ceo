import { useState, useEffect } from 'react';
import { campaignAPI } from '../services/api';
import { RefreshCw, Search, Filter, Eye, Calendar, X, Bot, User, Clock, CheckCircle, XCircle } from 'lucide-react';

export default function CampaignList() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [campaignDetails, setCampaignDetails] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  useEffect(() => {
    loadCampaigns();
  }, [statusFilter]);

  const loadCampaigns = async () => {
    setLoading(true);
    try {
      const data = await campaignAPI.listCampaigns(
        statusFilter !== 'all' ? statusFilter : null
      );
      
      // Handle both array response and object with campaigns property
      let campaignsList = [];
      if (Array.isArray(data)) {
        campaignsList = data;
      } else if (data && data.campaigns) {
        campaignsList = data.campaigns;
      }
      
      setCampaigns(campaignsList);
    } catch (error) {
      console.error('Error loading campaigns:', error);
      // Show error to user with better UX
      alert(`Failed to load campaigns: ${error.message || 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      draft: 'bg-gray-100 text-gray-800',
      in_progress: 'bg-blue-100 text-blue-800',
      pending_approval: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-blue-100 text-blue-800',
      completed: 'bg-purple-100 text-purple-800',
      stopped: 'bg-red-100 text-red-800',
      failed: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const filteredCampaigns = campaigns.filter(campaign => {
    // If no search term, include all campaigns
    if (!searchTerm.trim()) {
      return true;
    }
    const searchLower = searchTerm.toLowerCase();
    return (
      campaign.name?.toLowerCase().includes(searchLower) ||
      campaign.objective?.toLowerCase().includes(searchLower) ||
      campaign.id?.toLowerCase().includes(searchLower)
    );
  });

  const handleViewCampaign = async (campaignId) => {
    setSelectedCampaign(campaignId);
    setLoadingDetails(true);
    try {
      const details = await campaignAPI.getCampaign(campaignId);
      setCampaignDetails(details);
    } catch (error) {
      console.error('Error loading campaign details:', error);
      alert(`Failed to load campaign details: ${error.message || 'Unknown error'}`);
      setSelectedCampaign(null);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleCloseModal = () => {
    setSelectedCampaign(null);
    setCampaignDetails(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Campaigns</h1>
              <p className="text-gray-600 text-lg">View and manage all your marketing campaigns</p>
            </div>
            <button
              onClick={loadCampaigns}
              disabled={loading}
              className="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl shadow-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-md"
            >
              <RefreshCw className={`w-5 h-5 mr-2 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search campaigns by name or objective..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-gray-900 placeholder-gray-400"
              />
            </div>
            <div className="relative">
              <Filter className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-gray-900 bg-white appearance-none cursor-pointer"
              >
                <option value="all">All Statuses</option>
                <option value="draft">Draft</option>
                <option value="in_progress">In Progress</option>
                <option value="pending_approval">Pending Approval</option>
                <option value="approved">Approved</option>
                <option value="active">Active</option>
                <option value="completed">Completed</option>
                <option value="stopped">Stopped</option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>
        </div>

        {/* Campaigns List */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          {loading ? (
            <div className="text-center py-16">
              <RefreshCw className="w-12 h-12 animate-spin mx-auto text-blue-600 mb-4" />
              <p className="text-gray-600 text-lg font-medium">Loading campaigns...</p>
            </div>
          ) : filteredCampaigns.length === 0 ? (
            <div className="text-center py-16 px-4">
              <div className="max-w-md mx-auto">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Calendar className="w-8 h-8 text-gray-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No campaigns found</h3>
                <p className="text-gray-600">
                  {campaigns.length === 0
                    ? 'Create your first campaign to get started'
                    : `Found ${campaigns.length} campaign(s) but none match your search/filter. Try adjusting your criteria.`}
                </p>
              </div>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {filteredCampaigns.map((campaign) => (
                <div
                  key={campaign.id}
                  className="p-6 hover:bg-gray-50 transition-colors duration-200 group"
                >
                  <div className="flex items-start justify-between gap-6">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-3">
                        <h3 className="text-xl font-bold text-gray-900 truncate">
                          {campaign.name || 'Unnamed Campaign'}
                        </h3>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide flex-shrink-0 ${getStatusColor(
                            campaign.status
                          )}`}
                        >
                          {campaign.status || 'unknown'}
                        </span>
                      </div>
                      <p className="text-gray-600 mb-5 leading-relaxed line-clamp-2">
                        {campaign.objective}
                      </p>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {campaign.segment_id && (
                          <div className="bg-gray-50 rounded-lg p-3">
                            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Segment</p>
                            <p className="text-sm font-semibold text-gray-900 truncate">{campaign.segment_id}</p>
                          </div>
                        )}
                        {campaign.segment_size !== undefined && (
                          <div className="bg-gray-50 rounded-lg p-3">
                            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Size</p>
                            <p className="text-sm font-semibold text-gray-900">
                              {campaign.segment_size.toLocaleString()}
                            </p>
                          </div>
                        )}
                        {campaign.experiment_id && (
                          <div className="bg-gray-50 rounded-lg p-3">
                            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Experiment</p>
                            <p className="text-sm font-semibold text-gray-900 truncate">{campaign.experiment_id}</p>
                          </div>
                        )}
                        <div className="bg-gray-50 rounded-lg p-3">
                          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Compliance</p>
                          <p
                            className={`text-sm font-semibold ${
                              campaign.compliance_check_passed
                                ? 'text-green-600'
                                : 'text-amber-600'
                            }`}
                          >
                            {campaign.compliance_check_passed ? '✓ Passed' : '⏳ Pending'}
                          </p>
                        </div>
                      </div>
                    </div>
                    <button 
                      onClick={() => handleViewCampaign(campaign.id)}
                      className="inline-flex items-center px-5 py-2.5 bg-white border-2 border-gray-200 text-gray-700 font-medium rounded-xl hover:border-blue-500 hover:text-blue-600 transition-all duration-200 flex-shrink-0 group-hover:shadow-sm"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      <span>View</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Campaign Details Modal */}
        {selectedCampaign && (
          <div className="fixed inset-0 z-50 overflow-y-auto" onClick={handleCloseModal}>
            <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
              {/* Background overlay */}
              <div className="fixed inset-0 transition-opacity bg-gray-900 bg-opacity-75" onClick={handleCloseModal}></div>

              {/* Modal panel */}
              <div 
                className="inline-block align-bottom bg-white rounded-2xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-5xl sm:w-full"
                onClick={(e) => e.stopPropagation()}
              >
                {loadingDetails ? (
                  <div className="p-12 text-center">
                    <RefreshCw className="w-12 h-12 animate-spin mx-auto text-blue-600 mb-4" />
                    <p className="text-gray-600 text-lg font-medium">Loading campaign details...</p>
                  </div>
                ) : campaignDetails ? (
                  <div className="bg-white">
                    {/* Modal Header */}
                    <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-8 py-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h2 className="text-3xl font-bold text-white mb-2">
                            {campaignDetails.name || 'Unnamed Campaign'}
                          </h2>
                          <div className="flex items-center gap-3 flex-wrap">
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${getStatusColor(campaignDetails.status)}`}>
                              {campaignDetails.status || 'unknown'}
                            </span>
                            {campaignDetails.created_at && (
                              <span className="text-blue-100 text-sm flex items-center">
                                <Clock className="w-4 h-4 mr-1" />
                                Created: {new Date(campaignDetails.created_at).toLocaleString()}
                              </span>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={handleCloseModal}
                          className="ml-4 text-white hover:text-gray-200 transition-colors"
                        >
                          <X className="w-6 h-6" />
                        </button>
                      </div>
                    </div>

                    {/* Modal Content */}
                    <div className="p-8 max-h-[calc(100vh-200px)] overflow-y-auto">
                      {/* Campaign Objective */}
                      <div className="mb-8">
                        <h3 className="text-lg font-bold text-gray-900 mb-3">Campaign Objective</h3>
                        <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
                          <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                            {campaignDetails.objective || 'No objective provided'}
                          </p>
                        </div>
                      </div>

                      {/* Campaign Metadata */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                        {campaignDetails.segment_id && (
                          <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
                            <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Segment ID</p>
                            <p className="text-sm font-bold text-gray-900 break-all">{campaignDetails.segment_id}</p>
                          </div>
                        )}
                        {campaignDetails.segment_size !== undefined && (
                          <div className="bg-purple-50 rounded-xl p-4 border border-purple-200">
                            <p className="text-xs font-semibold text-purple-600 uppercase tracking-wide mb-2">Segment Size</p>
                            <p className="text-sm font-bold text-gray-900">{campaignDetails.segment_size.toLocaleString()}</p>
                          </div>
                        )}
                        {campaignDetails.experiment_id && (
                          <div className="bg-orange-50 rounded-xl p-4 border border-orange-200">
                            <p className="text-xs font-semibold text-orange-600 uppercase tracking-wide mb-2">Experiment ID</p>
                            <p className="text-sm font-bold text-gray-900 break-all">{campaignDetails.experiment_id}</p>
                          </div>
                        )}
                        <div className="bg-green-50 rounded-xl p-4 border border-green-200">
                          <p className="text-xs font-semibold text-green-600 uppercase tracking-wide mb-2">Compliance</p>
                          <p className={`text-sm font-bold ${campaignDetails.compliance_check_passed ? 'text-green-600' : 'text-amber-600'}`}>
                            {campaignDetails.compliance_check_passed ? (
                              <span className="flex items-center">
                                <CheckCircle className="w-4 h-4 mr-1" />
                                Passed
                              </span>
                            ) : (
                              <span className="flex items-center">
                                <XCircle className="w-4 h-4 mr-1" />
                                Pending
                              </span>
                            )}
                          </p>
                        </div>
                      </div>

                      {/* Agent Messages */}
                      {campaignDetails.messages && campaignDetails.messages.length > 0 && (
                        <div>
                          <h3 className="text-lg font-bold text-gray-900 mb-4">
                            Agent Messages ({campaignDetails.messages.length})
                          </h3>
                          <div className="space-y-4">
                            {campaignDetails.messages.map((message, index) => {
                              const isAgent = message.agent && message.agent !== 'user';
                              const agentColors = {
                                StrategyLead: 'bg-blue-100 text-blue-900 border-blue-300',
                                DataSegmenter: 'bg-purple-100 text-purple-900 border-purple-300',
                                ContentCreator: 'bg-green-100 text-green-900 border-green-300',
                                ComplianceOfficer: 'bg-yellow-100 text-yellow-900 border-yellow-300',
                                ExperimentRunner: 'bg-orange-100 text-orange-900 border-orange-300',
                              };
                              const messageColor = isAgent ? agentColors[message.agent] || 'bg-gray-100 text-gray-900 border-gray-300' : 'bg-gray-50 text-gray-800 border-gray-200';

                              return (
                                <div
                                  key={index}
                                  className={`rounded-xl p-5 border-2 ${messageColor} shadow-sm`}
                                >
                                  <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center space-x-3">
                                      {isAgent ? (
                                        <Bot className="w-5 h-5" />
                                      ) : (
                                        <User className="w-5 h-5" />
                                      )}
                                      <div>
                                        <span className="font-bold text-lg">
                                          {isAgent ? message.agent : 'User'}
                                        </span>
                                        {message.role && (
                                          <span className="text-xs text-gray-600 ml-2">({message.role})</span>
                                        )}
                                      </div>
                                    </div>
                                    {message.timestamp && (
                                      <span className="text-xs text-gray-500 font-medium">
                                        {new Date(message.timestamp).toLocaleString()}
                                      </span>
                                    )}
                                  </div>
                                  <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                                    {message.content || message.text || 'No content'}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Additional Info */}
                      <div className="mt-8 pt-6 border-t border-gray-200">
                        <h3 className="text-lg font-bold text-gray-900 mb-4">Additional Information</h3>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600 font-medium">Campaign ID:</span>
                            <span className="ml-2 text-gray-900 font-mono">{campaignDetails.id}</span>
                          </div>
                          <div>
                            <span className="text-gray-600 font-medium">Created By:</span>
                            <span className="ml-2 text-gray-900">{campaignDetails.created_by || 'System'}</span>
                          </div>
                          {campaignDetails.agents_involved && campaignDetails.agents_involved.length > 0 && (
                            <div className="col-span-2">
                              <span className="text-gray-600 font-medium">Agents Involved:</span>
                              <span className="ml-2 text-gray-900">{campaignDetails.agents_involved.join(', ')}</span>
                            </div>
                          )}
                          {campaignDetails.last_updated && (
                            <div>
                              <span className="text-gray-600 font-medium">Last Updated:</span>
                              <span className="ml-2 text-gray-900">{new Date(campaignDetails.last_updated).toLocaleString()}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

