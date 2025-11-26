import { useState } from 'react';
import { contentAPI } from '../services/api';
import { Shield, CheckCircle, XCircle, AlertTriangle, Loader2 } from 'lucide-react';

const CATEGORY_LABELS = {
  hate: 'Hate',
  violence: 'Violence',
  sexual: 'Sexual Content',
  self_harm: 'Self-Harm',
};

export default function ContentValidator() {
  const [content, setContent] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleValidate = async () => {
    if (!content.trim()) {
      setError('Please enter content to validate');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await contentAPI.validateContent(content);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to validate content');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setContent('');
    setResult(null);
    setError(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Content Safety Validator</h2>
        <p className="text-gray-600">
          Validate marketing content for safety, compliance, and brand guidelines
        </p>
      </div>

      {/* Input Form */}
      <div className="card">
        <div className="space-y-4">
          <div>
            <label className="label">Content to Validate</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste your marketing content here for safety and compliance validation..."
              rows="8"
              className="input-field font-mono text-sm"
            />
            <p className="text-xs text-gray-500 mt-1">
              {content.length} characters
            </p>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={handleValidate}
              disabled={loading || !content.trim()}
              className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Validating...</span>
                </>
              ) : (
                <>
                  <Shield className="w-4 h-4" />
                  <span>Validate Content</span>
                </>
              )}
            </button>
            {content && (
              <button onClick={handleClear} className="btn-secondary">
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="card bg-red-50 border-red-200">
          <div className="flex items-start space-x-3">
            <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-red-900">Error</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Validation Results */}
      {result && (
        <div className="space-y-4">
          {/* Overall Status */}
          <div
            className={`card ${
              result.is_safe
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}
          >
            <div className="flex items-start space-x-3">
              {result.is_safe ? (
                <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <h3
                  className={`font-semibold ${
                    result.is_safe ? 'text-green-900' : 'text-red-900'
                  }`}
                >
                  {result.is_safe ? 'Content is Safe' : 'Content Violations Detected'}
                </h3>
                <p
                  className={`text-sm mt-1 ${
                    result.is_safe ? 'text-green-700' : 'text-red-700'
                  }`}
                >
                  {result.is_safe
                    ? 'This content passed all safety and compliance checks.'
                    : 'This content contains violations that need to be addressed.'}
                </p>
              </div>
            </div>
          </div>

          {/* Violations */}
          {result.violations && result.violations.length > 0 && (
            <div className="card bg-yellow-50 border-yellow-200">
              <h3 className="font-semibold text-yellow-900 mb-3 flex items-center space-x-2">
                <AlertTriangle className="w-5 h-5" />
                <span>Violations Found</span>
              </h3>
              <ul className="space-y-2">
                {result.violations.map((violation, index) => (
                  <li key={index} className="text-sm text-yellow-800">
                    • {violation}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Category Scores */}
          {result.categories && (
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4">Safety Category Scores</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(result.categories).map(([category, score]) => {
                  const severity =
                    score >= 6
                      ? 'high'
                      : score >= 4
                      ? 'medium'
                      : score >= 2
                      ? 'low'
                      : 'none';
                  const colors = {
                    high: 'bg-red-100 text-red-800 border-red-300',
                    medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
                    low: 'bg-blue-100 text-blue-800 border-blue-300',
                    none: 'bg-green-100 text-green-800 border-green-300',
                  };

                  return (
                    <div
                      key={category}
                      className={`border rounded-lg p-4 ${colors[severity]}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">
                          {CATEGORY_LABELS[category] || category}
                        </span>
                        <span className="text-sm font-bold">Score: {score}/7</span>
                      </div>
                      <div className="w-full bg-white bg-opacity-50 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            severity === 'high'
                              ? 'bg-red-600'
                              : severity === 'medium'
                              ? 'bg-yellow-600'
                              : severity === 'low'
                              ? 'bg-blue-600'
                              : 'bg-green-600'
                          }`}
                          style={{ width: `${(score / 7) * 100}%` }}
                        />
                      </div>
                      <p className="text-xs mt-2 opacity-75">
                        {severity === 'high'
                          ? 'High risk - requires review'
                          : severity === 'medium'
                          ? 'Medium risk - monitor closely'
                          : severity === 'low'
                          ? 'Low risk - acceptable'
                          : 'No risk detected'}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Placeholder */}
      {!result && !loading && !error && (
        <div className="card">
          <div className="text-center py-12">
            <Shield className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 mb-2">Enter content to validate</p>
            <p className="text-sm text-gray-500">
              The validator checks for safety violations, brand compliance, and content quality
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

