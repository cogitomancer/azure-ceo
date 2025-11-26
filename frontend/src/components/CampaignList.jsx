import { useState, useEffect } from 'react';
import { campaignAPI } from '../services/api';
import { RefreshCw, Search, Filter, Eye, Calendar } from 'lucide-react';

export default function CampaignList() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    loadCampaigns();
  }, [statusFilter]);

  const loadCampaigns = async () => {
    setLoading(true);
    try {
      const data = await campaignAPI.listCampaigns(
        statusFilter !== 'all' ? statusFilter : null
      );
      setCampaigns(data.campaigns || []);
    } catch (error) {
      console.error('Error loading campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      draft: 'bg-gray-100 text-gray-800',
      pending_approval: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-blue-100 text-blue-800',
      completed: 'bg-purple-100 text-purple-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const filteredCampaigns = campaigns.filter(campaign =>
    campaign.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    campaign.objective?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Campaigns</h2>
            <p className="text-gray-600">View and manage all your marketing campaigns</p>
          </div>
          <button
            onClick={loadCampaigns}
            disabled={loading}
            className="btn-primary flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search campaigns..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input-field pl-10"
            >
              <option value="all">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="pending_approval">Pending Approval</option>
              <option value="approved">Approved</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Campaigns List */}
      <div className="card">
        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-primary-600 mb-4" />
            <p className="text-gray-600">Loading campaigns...</p>
          </div>
        ) : filteredCampaigns.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">No campaigns found</p>
            <p className="text-sm text-gray-500">
              {campaigns.length === 0
                ? 'Create your first campaign to get started'
                : 'Try adjusting your search or filter criteria'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredCampaigns.map((campaign) => (
              <div
                key={campaign.id}
                className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {campaign.name || 'Unnamed Campaign'}
                      </h3>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                          campaign.status
                        )}`}
                      >
                        {campaign.status || 'unknown'}
                      </span>
                    </div>
                    <p className="text-gray-600 mb-4">{campaign.objective}</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      {campaign.segment_id && (
                        <div>
                          <span className="text-gray-500">Segment:</span>
                          <span className="ml-2 font-medium">{campaign.segment_id}</span>
                        </div>
                      )}
                      {campaign.segment_size !== undefined && (
                        <div>
                          <span className="text-gray-500">Size:</span>
                          <span className="ml-2 font-medium">
                            {campaign.segment_size.toLocaleString()}
                          </span>
                        </div>
                      )}
                      {campaign.experiment_id && (
                        <div>
                          <span className="text-gray-500">Experiment:</span>
                          <span className="ml-2 font-medium">{campaign.experiment_id}</span>
                        </div>
                      )}
                      <div>
                        <span className="text-gray-500">Compliance:</span>
                        <span
                          className={`ml-2 font-medium ${
                            campaign.compliance_check_passed
                              ? 'text-green-600'
                              : 'text-red-600'
                          }`}
                        >
                          {campaign.compliance_check_passed ? 'Passed' : 'Pending'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <button className="btn-secondary flex items-center space-x-2 ml-4">
                    <Eye className="w-4 h-4" />
                    <span>View</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

