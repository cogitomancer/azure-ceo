import { useState } from 'react';
import { experimentAPI } from '../services/api';
import { Search, TrendingUp, BarChart3, AlertCircle } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function ExperimentAnalysis() {
  const [experimentId, setExperimentId] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    if (!experimentId.trim()) {
      setError('Please enter an experiment ID');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await experimentAPI.getAnalysis(experimentId);
      setAnalysis(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch experiment analysis');
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  // Mock data for visualization (replace with real data from API)
  const mockChartData = [
    { name: 'Day 1', VariantA: 120, VariantB: 135, VariantC: 110 },
    { name: 'Day 2', VariantA: 145, VariantB: 160, VariantC: 130 },
    { name: 'Day 3', VariantA: 165, VariantB: 180, VariantC: 150 },
    { name: 'Day 4', VariantA: 180, VariantB: 200, VariantC: 170 },
    { name: 'Day 5', VariantA: 195, VariantB: 220, VariantC: 185 },
  ];

  const mockConversionData = [
    { name: 'Variant A', conversions: 805, visits: 10000, rate: 8.05 },
    { name: 'Variant B', conversions: 895, visits: 10000, rate: 8.95 },
    { name: 'Variant C', conversions: 745, visits: 10000, rate: 7.45 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Experiment Analysis</h2>
        <p className="text-gray-600">
          Analyze A/B test results and view statistical significance
        </p>
      </div>

      {/* Search Form */}
      <div className="card">
        <div className="flex space-x-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={experimentId}
              onChange={(e) => setExperimentId(e.target.value)}
              placeholder="Enter experiment ID (e.g., exp_abc123)"
              className="input-field pl-10"
              onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="btn-primary flex items-center space-x-2"
          >
            <BarChart3 className="w-4 h-4" />
            <span>{loading ? 'Analyzing...' : 'Analyze'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="card bg-red-50 border-red-200">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-red-900">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && (
        <div className="space-y-6">
          {/* Statistical Analysis */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <TrendingUp className="w-5 h-5" />
              <span>Statistical Analysis</span>
            </h3>
            {analysis.analysis && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-sm text-blue-600 font-medium">P-Value</div>
                    <div className="text-2xl font-bold text-blue-900">
                      {analysis.analysis.p_value?.toFixed(4) || 'N/A'}
                    </div>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-sm text-green-600 font-medium">Z-Score</div>
                    <div className="text-2xl font-bold text-green-900">
                      {analysis.analysis.z_score?.toFixed(2) || 'N/A'}
                    </div>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <div className="text-sm text-purple-600 font-medium">Confidence Level</div>
                    <div className="text-2xl font-bold text-purple-900">
                      {(analysis.analysis.confidence_level * 100)?.toFixed(1) || '95'}%
                    </div>
                  </div>
                </div>
                {analysis.recommendation && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="font-medium text-gray-900 mb-2">Recommendation</div>
                    <p className="text-sm text-gray-700">{analysis.recommendation}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Conversion Rate Chart */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversion Rates</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={mockConversionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="rate" fill="#0ea5e9" name="Conversion Rate (%)" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Daily Performance Chart */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Performance</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={mockChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="VariantA" stroke="#3b82f6" name="Variant A" />
                  <Line type="monotone" dataKey="VariantB" stroke="#10b981" name="Variant B" />
                  <Line type="monotone" dataKey="VariantC" stroke="#f59e0b" name="Variant C" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Detailed Results Table */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Detailed Results</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Variant
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Conversions
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Visits
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rate
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {mockConversionData.map((variant) => (
                    <tr key={variant.name}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {variant.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {variant.conversions.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {variant.visits.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {variant.rate}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            variant.name === 'Variant B'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {variant.name === 'Variant B' ? 'Winner' : 'Active'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Placeholder when no analysis */}
      {!analysis && !loading && !error && (
        <div className="card">
          <div className="text-center py-12">
            <BarChart3 className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 mb-2">Enter an experiment ID to view analysis</p>
            <p className="text-sm text-gray-500">
              Example: exp_abc123def456
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

