import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  { id: 'uploaded', label: 'Uploaded', icon: Zap, duration: '1-2s' },
  { id: 'validating_duplicates', label: 'Duplicate Detection', icon: Shield, duration: '2-3s' },
  { id: 'validating_consistency', label: 'Consistency Check', icon: CheckCircle, duration: '3-5s' },
  { id: 'validating_form', label: 'Form Validation', icon: Award, duration: '2-3s' },
  { id: 'completed', label: 'Completed', icon: CheckCircle, duration: '1s' },
];

export default function ProcessingStatusPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const processingInitiatedRef = useRef(false); // Prevent duplicate processing attempts
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [processAttempted, setProcessAttempted] = useState(false);
  const [extractedFormData, setExtractedFormData] = useState(null);
  const [extracting, setExtracting] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await submissionAPI.getStatus(id);
      const data = response.data;
      
      // Normalize status values for backwards compatibility
      // Convert old format (pass/fail) to new format (completed/failed)
      if (data.status === 'pass') {
        data.status = 'completed';
      } else if (data.status === 'fail') {
        data.status = 'failed';
      }
      
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
  }, [id]);

  const extractAndProcess = async () => {
    if (extracting || processing || !submission || submission.status !== 'uploaded') return;
    
    setExtracting(true);
    try {
      // Step 1: Extract Form 44 data from PDF
      console.log('[EXTRACT] Starting form extraction for submission:', id);
      console.log('[EXTRACT] Submission status:', submission.status);
      const extractResponse = await submissionAPI.extractForm44(id);
      
      if (extractResponse.status === 200) {
        const formData = extractResponse.data.form44_data;
        setExtractedFormData(formData);
        console.log('[EXTRACT] ✓ Form 44 data extracted successfully:', formData);
        console.log('[EXTRACT] Extracted field count:', Object.keys(formData).length);
        
        // Step 2: Process with extracted data
        setExtracting(false);
        await triggerProcessingWithData(formData);
      }
    } catch (error) {
      console.warn('[EXTRACT] Form extraction failed:', error.message);
      console.log('[EXTRACT] Error details:', error.response?.status, error.response?.data);
      console.warn('[EXTRACT] Falling back to processing without extracted data');
      setExtracting(false);
      // Fall back to processing without extracted data
      await triggerProcessing();
    }
  };

  const triggerProcessingWithData = async (formData) => {
    if (processing || !submission) return;
    
    setProcessing(true);
    console.log('[PROCESS] Starting processing with extracted data for submission:', id);
    console.log('[PROCESS] Form data keys:', Object.keys(formData).length > 0 ? Object.keys(formData) : 'EMPTY');
    try {
      const response = await submissionAPI.processSubmission(id, { form_data: formData });
      console.log('[PROCESS] ✓ Processing response received:', response.status);
      if (response.status === 200) {
        toast.success('Processing started with extracted Form 44 data!');
        await fetchStatus();
      }
    } catch (error) {
      console.error('[PROCESS] ✗ Processing failed:', error.message);
      console.error('[PROCESS] Error status:', error.response?.status);
      console.error('[PROCESS] Error response:', error.response?.data);
      console.error('[PROCESS] Submission ID:', id);
      const errorMsg = error.response?.data?.error || error.message || 'Failed to process submission';
      toast.error(errorMsg);
      console.error('Processing error:', error);
    } finally {
      setProcessing(false);
    }
  };

  const triggerProcessing = async () => {
    if (processing || !submission || submission.status !== 'uploaded') return;
    
    setProcessing(true);
    console.log('[PROCESS] Starting processing without extracted data for submission:', id);
    try {
      const response = await submissionAPI.processSubmission(id);
      console.log('[PROCESS] ✓ Processing response received:', response.status);
      if (response.status === 200) {
        toast.success('Processing started!');
        // Refresh immediately to see updated status
        await fetchStatus();
      }
    } catch (error) {
      console.error('[PROCESS] ✗ Processing failed:', error.message);
      console.error('[PROCESS] Error status:', error.response?.status);
      console.error('[PROCESS] Error data:', error.response?.data);
      const errorMsg = error.response?.data?.error || error.message || 'Failed to process submission';
      toast.error(errorMsg);
      console.error('Processing error:', error);
    } finally {
      setProcessing(false);
    }
  };

  const getCurrentStage = () => {
    if (!submission) return 0;
    const status = submission.status;
    
    // Map actual statuses to progress
    if (status === 'completed' || status === 'pass') return processingStages.length;
    if (status === 'failed' || status === 'fail') return 0;
    
    const stageIdx = processingStages.findIndex((s) => s.id === status);
    return stageIdx >= 0 ? stageIdx + 1 : 1; // Default to 1 if status not recognized
  };

  const isStageCompleted = (stageId) => {
    if (!submission) return false;
    const status = submission.status;
    
    // When failed, all stages except the final one are "completed", but final stage failed
    if (status === 'failed' || status === 'fail') {
      // All stages before "completed" stage
      if (stageId !== 'completed') {
        return true; // All intermediate stages completed
      }
      return false; // Final stage failed
    }
    
    // When completed, all stages are completed
    if (status === 'completed' || status === 'pass') {
      return true;
    }
    
    // For other statuses (in progress), show stages that have been completed
    const currentIdx = processingStages.findIndex((s) => s.id === status);
    const stageIdx = processingStages.findIndex((s) => s.id === stageId);
    return stageIdx < currentIdx;
  };

  const isStageInProgress = (stageId) => {
    if (!submission) return false;
    return submission.status === stageId;
  };

  const getProgressPercentage = () => {
    if (!submission) return 0;
    const status = submission.status;
    
    if (status === 'completed' || status === 'pass') return 100;
    // Show 80% progress for failed - indicates most checks ran but one failed
    if (status === 'failed' || status === 'fail') return 80;
    
    const stage = getCurrentStage();
    return Math.max(0, (stage - 1) / processingStages.length * 100);
  };

  useEffect(() => {
    fetchStatus();
    const interval = autoRefresh ? setInterval(fetchStatus, 2000) : null;
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [id, autoRefresh, fetchStatus]);

  // Reset processing flag when submission ID changes
  useEffect(() => {
    processingInitiatedRef.current = false;
  }, [id]);

  // Auto-trigger extraction and processing when uploaded status is detected
  useEffect(() => {
    // Only start processing once per submission, when status is 'uploaded'
    if (submission?.status === 'uploaded' && !processingInitiatedRef.current && !processing && !extracting) {
      processingInitiatedRef.current = true; // Mark as initiated to prevent re-triggering
      setProcessAttempted(true);
      extractAndProcess();
    }
  }, [submission?.status]); // Minimal deps - only respond to status changes

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
                    {(submission?.status === 'completed' || submission?.status === 'pass') && (
                      <span className="badge badge-success">✓ Completed</span>
                    )}
                    {(submission?.status === 'failed' || submission?.status === 'fail') && (
                      <span className="badge badge-error">✗ Failed</span>
                    )}
                    {submission?.status !== 'completed' && submission?.status !== 'failed' && submission?.status !== 'pass' && submission?.status !== 'fail' && (
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

                  {/* Process Now Button - Show only if uploaded and not processing */}
                  {submission?.status === 'uploaded' && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <AlertCircle className="w-5 h-5 text-yellow-600" />
                        <div>
                          <p className="font-semibold text-yellow-900">Ready to Process</p>
                          <p className="text-sm text-yellow-700">Click the button to extract Form 44 data and start processing</p>
                        </div>
                      </div>
                      <button
                        onClick={extractAndProcess}
                        disabled={processing || extracting}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                      >
                        {processing || extracting ? (
                          <>
                            <span className="animate-spin">⟳</span>
                            <span>{extracting ? 'Extracting...' : 'Processing...'}</span>
                          </>
                        ) : (
                          <>
                            <Zap className="w-4 h-4" />
                            <span>Process Now</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}

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

                  {/* Extracted Form Data */}
                  {extractedFormData && Object.keys(extractedFormData).length > 0 && (
                    <div className="bg-blue-50 rounded-lg p-4 space-y-3 border-l-4 border-blue-500">
                      <h3 className="font-semibold text-gray-900 flex items-center space-x-2">
                        <span>✓ Extracted Form 44 Data</span>
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {Object.entries(extractedFormData).map(([key, value]) => (
                          <div key={key} className="bg-white rounded p-3 border border-blue-100">
                            <p className="text-xs text-gray-600 uppercase font-semibold">{key.replace(/_/g, ' ')}</p>
                            <p className="font-medium text-gray-900 mt-1 break-words">
                              {value ? String(value) : '—'}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

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
