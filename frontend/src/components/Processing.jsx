import { useState, useEffect } from 'react';
import { FiRefreshCw, FiLoader, FiCheckCircle, FiAlertCircle } from 'react-icons/fi';
import { submissionAPI } from '../services/api';
import { formatDistanceToNow } from 'date-fns';

export default function Processing({ submissionId, onProcessingComplete }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    if (!submissionId) return;

    // Fetch initial status
    fetchStatus();

    // Auto-refresh if still processing
    const interval = setInterval(() => {
      if (autoRefresh) {
        fetchStatus();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [submissionId, autoRefresh]);

  const fetchStatus = async () => {
    try {
      const response = await submissionAPI.getStatus(submissionId);
      const data = response.data;
      setStatus(data);
      setError('');

      // Stop auto-refresh when completed or failed
      if (data.status === 'completed' || data.status === 'failed') {
        setAutoRefresh(false);
        if (onProcessingComplete && data.status === 'completed') {
          onProcessingComplete();
        }
      }

      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Error fetching status');
      setLoading(false);
    }
  };

  if (!status) {
    return (
      <div className="card p-8 text-center">
        <FiLoader className="mx-auto text-4xl text-gray-400 mb-4 animate-spin" />
        <p className="text-gray-600">Loading status...</p>
      </div>
    );
  }

  const getStatusColor = (st) => {
    switch (st) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'danger';
      case 'processing':
      case 'extracting_text':
      case 'anonymizing':
      case 'summarizing':
      case 'validating_compliance':
        return 'warning';
      default:
        return 'warning';
    }
  };

  const getStatusIcon = (st) => {
    switch (st) {
      case 'completed':
        return <FiCheckCircle className="text-success-600 text-2xl" />;
      case 'failed':
        return <FiAlertCircle className="text-danger-600 text-2xl" />;
      default:
        return <FiLoader className="text-warning-600 text-2xl animate-spin" />;
    }
  };

  const getProgressPercentage = (st) => {
    const stages = {
      pending: 0,
      processing: 20,
      extracting_text: 25,
      anonymizing: 50,
      summarizing: 75,
      validating_compliance: 90,
      completed: 100,
      failed: 100,
    };
    return stages[st] || 0;
  };

  const statusLabel = status.status
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (l) => l.toUpperCase());

  return (
    <div className="card p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Processing Status</h2>
        <button
          onClick={fetchStatus}
          disabled={loading}
          className="btn-secondary flex items-center gap-2"
        >
          <FiRefreshCw className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Submission ID */}
      <div className="bg-gray-50 rounded-lg p-4">
        <p className="text-sm text-gray-600">Submission ID</p>
        <p className="font-mono break-all text-sm">{submissionId}</p>
      </div>

      {/* Status Badge */}
      <div className="flex items-center gap-4">
        {getStatusIcon(status.status)}
        <div>
          <p className="text-sm text-gray-600">Current Status</p>
          <p className="text-xl font-bold">
            <span className={`badge badge-${getStatusColor(status.status)}`}>
              {statusLabel}
            </span>
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      <div>
        <div className="flex justify-between mb-2">
          <p className="text-sm text-gray-600">Progress</p>
          <p className="text-sm font-medium">{getProgressPercentage(status.status)}%</p>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              status.status === 'completed'
                ? 'bg-success-600'
                : status.status === 'failed'
                ? 'bg-danger-600'
                : 'bg-primary-600'
            }`}
            style={{ width: `${getProgressPercentage(status.status)}%` }}
          />
        </div>
      </div>

      {/* Timeline */}
      <div className="space-y-4">
        <p className="text-sm font-medium text-gray-700">Processing Timeline</p>
        
        <div className="space-y-3">
          {/* Upload */}
          <div className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className="w-8 h-8 rounded-full bg-success-600 text-white flex items-center justify-center text-sm">
                ✓
              </div>
              <div className="w-0.5 h-12 bg-gray-300 my-2" />
            </div>
            <div>
              <p className="font-medium text-gray-900">Document Uploaded</p>
              <p className="text-sm text-gray-600">
                {status.created_at
                  ? formatDistanceToNow(new Date(status.created_at), { addSuffix: true })
                  : 'Just now'}
              </p>
            </div>
          </div>

          {/* OCR */}
          <div className="flex gap-4">
            <div className="flex flex-col items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                  ['extracting_text', 'anonymizing', 'summarizing', 'validating_compliance', 'completed'].includes(
                    status.status
                  )
                    ? 'bg-success-600 text-white'
                    : 'bg-gray-300 text-gray-600'
                }`}
              >
                {['extracting_text', 'anonymizing', 'summarizing', 'validating_compliance', 'completed'].includes(
                  status.status
                ) ? (
                  '✓'
                ) : status.status === 'extracting_text' ? (
                  <FiLoader className="animate-spin" />
                ) : (
                  '○'
                )}
              </div>
              <div className="w-0.5 h-12 bg-gray-300 my-2" />
            </div>
            <div>
              <p className="font-medium text-gray-900">Text Extraction (OCR)</p>
              <p className="text-sm text-gray-600">
                {status.status === 'extracting_text' ? 'In progress...' : 'Completed'}
              </p>
            </div>
          </div>

          {/* Anonymization */}
          <div className="flex gap-4">
            <div className="flex flex-col items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                  ['anonymizing', 'summarizing', 'validating_compliance', 'completed'].includes(status.status)
                    ? 'bg-success-600 text-white'
                    : 'bg-gray-300 text-gray-600'
                }`}
              >
                {['anonymizing', 'summarizing', 'validating_compliance', 'completed'].includes(status.status) ? (
                  '✓'
                ) : status.status === 'anonymizing' ? (
                  <FiLoader className="animate-spin" />
                ) : (
                  '○'
                )}
              </div>
              <div className="w-0.5 h-12 bg-gray-300 my-2" />
            </div>
            <div>
              <p className="font-medium text-gray-900">DPDP Anonymization</p>
              <p className="text-sm text-gray-600">
                {status.status === 'anonymizing' ? 'In progress...' : 'Pending'}
              </p>
            </div>
          </div>

          {/* Summarization */}
          <div className="flex gap-4">
            <div className="flex flex-col items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                  ['summarizing', 'validating_compliance', 'completed'].includes(status.status)
                    ? 'bg-success-600 text-white'
                    : 'bg-gray-300 text-gray-600'
                }`}
              >
                {['summarizing', 'validating_compliance', 'completed'].includes(status.status) ? (
                  '✓'
                ) : status.status === 'summarizing' ? (
                  <FiLoader className="animate-spin" />
                ) : (
                  '○'
                )}
              </div>
              <div className="w-0.5 h-12 bg-gray-300 my-2" />
            </div>
            <div>
              <p className="font-medium text-gray-900">Summarization</p>
              <p className="text-sm text-gray-600">
                {status.status === 'summarizing' ? 'In progress...' : 'Pending'}
              </p>
            </div>
          </div>

          {/* Compliance */}
          <div className="flex gap-4">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                ['validating_compliance', 'completed'].includes(status.status)
                  ? 'bg-success-600 text-white'
                  : 'bg-gray-300 text-gray-600'
              }`}
            >
              {['validating_compliance', 'completed'].includes(status.status) ? (
                '✓'
              ) : status.status === 'validating_compliance' ? (
                <FiLoader className="animate-spin" />
              ) : (
                '○'
              )}
            </div>
            <div>
              <p className="font-medium text-gray-900">Compliance Validation</p>
              <p className="text-sm text-gray-600">
                {status.status === 'validating_compliance' ? 'In progress...' : 'Pending'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {status.error_message && (
        <div className="alert alert-danger flex items-start gap-3">
          <span className="text-lg">⚠️</span>
          <div>
            <p className="font-medium">Processing Error</p>
            <p className="text-sm mt-1">{status.error_message}</p>
          </div>
        </div>
      )}

      {/* Processing Duration */}
      {status.processing_duration && (
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-600">Processing Time</p>
          <p className="text-lg font-bold">{status.processing_duration.toFixed(2)} seconds</p>
        </div>
      )}
    </div>
  );
}
