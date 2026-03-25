import React, { useState, useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  RotateCw,
  Zap,
  Shield,
  Award
} from 'lucide-react';

import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import { submissionAPI } from '../services/api';

const processingStages = [
  { id: 'extracting_text', label: 'OCR Extraction', icon: Zap, duration: '5-10s' },
  { id: 'anonymizing', label: 'Anonymization', icon: Shield, duration: '2-3s' },
  { id: 'summarizing', label: 'Summarization', icon: CheckCircle, duration: '10-15s' },
  { id: 'validating_compliance', label: 'Compliance Validation', icon: Award, duration: '1-2s' },
];

export default function ProcessingStatusPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchStatus();
    const interval = autoRefresh ? setInterval(fetchStatus, 3000) : null;
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [id, autoRefresh]);

  const fetchStatus = async () => {
    try {
      const response = await submissionAPI.getStatus(id);
      const data = response.data;
      setSubmission(data);

      // Stop auto-refresh when completed or failed
      if (data.status === 'completed' || data.status === 'failed') {
        setAutoRefresh(false);
      }

      setLoading(false);
    } catch (error) {
      toast.error('Failed to fetch status');
      console.error(error);
      setLoading(false);
    }
  };

  const getCurrentStage = () => {
    if (!submission) return 0;
    return processingStages.findIndex((s) => s.id === submission.status) + 1;
  };

  const isStageCompleted = (stageId) => {
    if (!submission) return false;
    const currentIdx = processingStages.findIndex((s) => s.id === submission.status);
    const stageIdx = processingStages.findIndex((s) => s.id === stageId);
    return stageIdx < currentIdx || submission.status === 'completed';
  };

  const isStageInProgress = (stageId) => {
    if (!submission) return false;
    return submission.status === stageId;
  };

  const getProgressPercentage = () => {
    if (!submission) return 0;
    if (submission.status === 'completed') return 100;
    if (submission.status === 'failed') return 0;
    return ((getCurrentStage() - 1) / processingStages.length) * 100;
  };

  if (loading) {
    return (
      <>
        <Helmet>
          <title>Processing Status - SwasthyaAI Regulator</title>
        </Helmet>
        <div className="flex h-screen bg-gray-100">
          <Sidebar isOpen={sidebarOpen} />
          <div className="flex-1 flex flex-col overflow-hidden">
            <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
            <main className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin inline-block text-4xl mb-4">⏳</div>
                <p className="text-gray-600">Loading processing status...</p>
              </div>
            </main>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Helmet>
        <title>Processing Status - SwasthyaAI Regulator</title>
      </Helmet>

      <div className="flex h-screen bg-gray-100">
        <Sidebar isOpen={sidebarOpen} />

        <div className="flex-1 flex flex-col overflow-hidden">
          <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

          {/* Main Content */}
          <main className="flex-1 overflow-y-auto">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {/* Page Header */}
              <div className="mb-8">
                <h2 className="text-3xl font-bold text-gray-900">Processing Status</h2>
                <p className="text-gray-600 mt-2">Real-time document processing progress</p>
              </div>

              {/* Status Card */}
              <div className="card mb-8">
                <div className="card-header flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{submission?.filename}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Submission ID: {id}
                    </p>
                  </div>
                  <div>
                    {submission?.status === 'completed' && (
                      <span className="badge badge-success">✓ Completed</span>
                    )}
                    {submission?.status === 'failed' && (
                      <span className="badge badge-error">✗ Failed</span>
                    )}
                    {submission?.status !== 'completed' && submission?.status !== 'failed' && (
                      <span className="badge badge-info animate-pulse">◉ Processing</span>
                    )}
                  </div>
                </div>

                <div className="card-body space-y-8">
                  {/* Overall Progress */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <p className="font-medium text-gray-900">Overall Progress</p>
                      <p className="text-sm font-semibold text-blue-600">
                        {Math.round(getProgressPercentage())}%
                      </p>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${getProgressPercentage()}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Processing Stages */}
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-6">Processing Pipeline</h3>
                    <div className="space-y-4">
                      {processingStages.map((stage, idx) => {
                        const Icon = stage.icon;
                        const isCompleted = isStageCompleted(stage.id);
                        const isInProgress = isStageInProgress(stage.id);

                        return (
                          <div
                            key={stage.id}
                            className={`p-4 rounded-lg border-2 transition-all ${
                              isCompleted
                                ? 'bg-green-50 border-green-200'
                                : isInProgress
                                ? 'bg-blue-50 border-blue-200 border-dashed'
                                : 'bg-gray-50 border-gray-200'
                            }`}
                          >
                            <div className="flex items-start space-x-4">
                              {/* Stage Icon */}
                              <div
                                className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                                  isCompleted
                                    ? 'bg-green-500 text-white'
                                    : isInProgress
                                    ? 'bg-blue-500 text-white animate-pulse'
                                    : 'bg-gray-300 text-gray-600'
                                }`}
                              >
                                {isCompleted ? (
                                  <CheckCircle className="w-6 h-6" />
                                ) : isInProgress ? (
                                  <RotateCw className="w-6 h-6 animate-spin" />
                                ) : (
                                  <Icon className="w-6 h-6" />
                                )}
                              </div>

                              {/* Stage Info */}
                              <div className="flex-1">
                                <div className="flex items-center justify-between">
                                  <p className="font-semibold text-gray-900">{stage.label}</p>
                                  {isInProgress && (
                                    <p className="text-sm font-medium text-blue-600">In Progress...</p>
                                  )}
                                  {isCompleted && (
                                    <p className="text-sm font-medium text-green-600">✓ Completed</p>
                                  )}
                                </div>
                                <p className="text-sm text-gray-600 mt-1">
                                  Estimated duration: {stage.duration}
                                </p>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Submission Details */}
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <h3 className="font-semibold text-gray-900">Details</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-gray-600">Document Type</p>
                        <p className="font-medium text-gray-900">
                          {submission?.submission_type || 'form_44'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600">Elapsed Time</p>
                        <p className="font-medium text-gray-900">
                          {submission?.processing_duration
                            ? `${submission.processing_duration.toFixed(1)}s`
                            : 'Calculating...'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600">Status</p>
                        <p className="font-medium text-gray-900 capitalize">
                          {submission?.status?.replace(/_/g, ' ')}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600">Uploaded</p>
                        <p className="font-medium text-gray-900">
                          {new Date(submission?.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Error Message */}
                  {submission?.status === 'failed' && submission?.error_message && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
                      <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <h3 className="font-semibold text-red-900">Processing Failed</h3>
                        <p className="text-sm text-red-700 mt-1">{submission.error_message}</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="card-footer flex items-center justify-between">
                  <button
                    onClick={fetchStatus}
                    className="btn-secondary flex items-center space-x-2"
                  >
                    <RotateCw className="w-4 h-4" />
                    <span>Refresh</span>
                  </button>

                  {submission?.status === 'completed' && (
                    <button
                      onClick={() => navigate(`/submission/${id}/results`)}
                      className="btn-primary flex items-center space-x-2"
                    >
                      <span>View Results</span>
                      <CheckCircle className="w-4 h-4" />
                    </button>
                  )}

                  {submission?.status === 'failed' && (
                    <button
                      onClick={() => navigate('/')}
                      className="btn-secondary"
                    >
                      Go Back
                    </button>
                  )}
                </div>
              </div>

              {/* Auto-refresh Status */}
              <div className="text-center text-sm text-gray-600 p-4 bg-white rounded-lg border border-gray-200">
                {autoRefresh && submission?.status !== 'completed' && submission?.status !== 'failed' ? (
                  <p>📡 Auto-refreshing every 3 seconds...</p>
                ) : (
                  <p>Status updates paused. Click refresh to update.</p>
                )}
              </div>
            </div>
          </main>
        </div>
      </div>
    </>
  );
}
