import React, { useState, useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  Download,
  FileText,
  BarChart3,
  Shield,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  ArrowLeft,
  Loader,
  Lock,
  TrendingUp,
} from 'lucide-react';

import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import { submissionAPI } from '../services/api';

export default function ResultsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [results, setResults] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showFullText, setShowFullText] = useState(false);
  const [activeTab, setActiveTab] = useState('summary');
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    fetchStatus();
    
    // Setup polling for async tasks
    const pollInterval = setInterval(() => {
      fetchStatus();
    }, 2000);
    
    return () => clearInterval(pollInterval);
  }, [id]);

  useEffect(() => {
    // Auto-fetch full results when status completes
    if (status?.status === 'completed' && !results) {
      fetchResults();
    }
  }, [status?.status]);

  const fetchStatus = async () => {
    try {
      const res = await submissionAPI.getStatus(id);
      setStatus(res.data);
      setLoading(false);
      
      if (res.data.status === 'completed' && !results) {
        fetchResults();
      }
    } catch (error) {
      console.error('Error fetching status:', error);
      setLoading(false);
    }
  };

  const fetchResults = async () => {
    try {
      const res = await submissionAPI.getResults(id);
      setResults(res.data);
    } catch (error) {
      if (error.response?.status === 404) {
        toast.error('Results not found');
        navigate('/dashboard');
      } else {
        toast.error('Failed to fetch results');
      }
    }
  };

  const downloadResults = async () => {
    try {
      const content = generateResultsDocument();
      
      const element = document.createElement('a');
      const file = new Blob([content], { type: 'text/plain' });
      element.href = URL.createObjectURL(file);
      element.download = `results-${id}-${Date.now()}.txt`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      toast.success('Results downloaded');
    } catch (error) {
      toast.error('Failed to download results');
    }
  };

  const generateResultsDocument = () => {
    return `
SWASTHYAAI REGULATOR - PROCESSING RESULTS
==========================================

SUBMISSION DETAILS
------------------
Submission ID: ${id}
Filename: ${status?.filename || 'N/A'}
Status: ${status?.status || 'N/A'}
Created: ${status?.created_at || 'N/A'}

EXTRACTION RESULTS
------------------
Quality: ${results?.extraction?.quality || 'N/A'}
Confidence: ${results?.extraction?.confidence || 'N/A'}
Method: ${results?.extraction?.method || 'N/A'}
Pages: ${results?.extraction?.pages || 'N/A'}

ANONYMIZATION
--------------
PII Detected: ${Object.keys(results?.pii_stats || {}).length > 0 ? 'Yes' : 'No'}
${Object.entries(results?.pii_stats || {})
  .map(([type, count]) => `${type}: ${count} occurrences`)
  .join('\n')}

K-Anonymity: ${results?.anonymization?.k_anonymity || 'N/A'}
L-Diversity: ${results?.anonymization?.l_diversity || 'N/A'}
T-Closeness: ${results?.anonymization?.t_closeness || 'N/A'}

SUMMARIZATION
--------------
${results?.summary || 'No summary available'}

KEY FINDINGS
------------
${(results?.key_findings || []).length > 0
  ? results.key_findings.map((f, i) => `${i + 1}. ${f}`).join('\n')
  : 'No specific findings'}

COMPLIANCE STATUS
-----------------
Overall Score: ${results?.compliance?.overall_score || 0}%
Compliant: ${results?.compliance?.is_compliant ? 'Yes' : 'No'}
Status: ${results?.compliance?.status || 'N/A'}

Generated: ${new Date().toLocaleString()}
    `;
  };

  if (loading && !status) {
    return (
      <>
        <Helmet>
          <title>Results - SwasthyaAI Regulator</title>
        </Helmet>
        <div className="flex h-screen bg-gray-100">
          <Sidebar isOpen={sidebarOpen} />
          <div className="flex-1 flex flex-col overflow-hidden">
            <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
            <main className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <Loader className="animate-spin inline-block text-4xl mb-4 text-primary-500" style={{fontSize: '50px'}} />
                <p className="text-gray-600">Loading results...</p>
              </div>
            </main>
          </div>
        </div>
      </>
    );
  }

  // Processing status overlay for async tasks
  if (status?.status !== 'completed' && status?.status !== 'failed') {
    return (
      <>
        <Helmet>
          <title>Processing - SwasthyaAI Regulator</title>
        </Helmet>
        <div className="flex h-screen bg-gray-100">
          <Sidebar isOpen={sidebarOpen} />
          <div className="flex-1 flex flex-col overflow-hidden">
            <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
            <main className="flex-1 overflow-y-auto">
              <div className="max-w-4xl mx-auto p-6 h-full flex items-center justify-center">
                <div className="bg-white rounded-lg shadow-lg p-12 text-center max-w-md w-full">
                  <Loader className="animate-spin text-6xl mx-auto mb-6 text-primary-500" style={{fontSize: '60px'}} />
                  <h2 className="text-2xl font-bold mb-4">Processing Document</h2>
                  <p className="text-gray-600 mb-4">
                    Status: <span className="font-semibold capitalize">{status?.current_stage}</span>
                  </p>
                  
                  {/* Progress indicator */}
                  <div className="mb-6">
                    <ProcessingProgressBar stage={status?.current_stage} />
                  </div>
                  
                  {status?.async_mode && (
                    <p className="text-sm text-gray-500">
                      Task ID: {status?.task_id}
                    </p>
                  )}
                  
                  <button
                    onClick={() => navigate('/dashboard')}
                    className="mt-6 btn btn-secondary w-full"
                  >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Dashboard
                  </button>
                </div>
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
        <title>Results - SwasthyaAI Regulator</title>
      </Helmet>
      <div className="flex h-screen bg-gray-100">
        <Sidebar isOpen={sidebarOpen} />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
          <main className="flex-1 overflow-y-auto">
            <div className="max-w-6xl mx-auto p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <button
                    onClick={() => navigate('/dashboard')}
                    className="text-primary-500 hover:text-primary-600 mr-4"
                  >
                    <ArrowLeft className="w-6 h-6" />
                  </button>
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900">{status?.filename}</h1>
                    <p className="text-sm text-gray-500 mt-1">ID: {id}</p>
                  </div>
                </div>
                <button
                  onClick={downloadResults}
                  className="btn btn-primary"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download Results
                </button>
              </div>

              {/* Status Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <StatusCard
                  label="Status"
                  value={status?.status}
                  icon={status?.status === 'completed' ? CheckCircle : AlertCircle}
                  color={status?.status === 'completed' ? 'green' : 'red'}
                />
                <StatusCard
                  label="Extraction"
                  value={results?.extraction?.quality || 'N/A'}
                  icon={FileText}
                  color="blue"
                />
                <StatusCard
                  label="PII Found"
                  value={Object.keys(results?.pii_stats || {}).length}
                  icon={Lock}
                  color="orange"
                />
                <StatusCard
                  label="Compliance"
                  value={`${Math.round(results?.compliance?.overall_score || 0)}%`}
                  icon={Shield}
                  color={results?.compliance?.is_compliant ? 'green' : 'red'}
                />
              </div>

              {/* Tabs */}
              <div className="card mb-6">
                <div className="flex border-b border-gray-200">
                  {[
                    { id: 'summary', label: 'Summary' },
                    { id: 'extraction', label: 'Extraction' },
                    { id: 'anonymization', label: 'Anonymization' },
                    { id: 'compliance', label: 'Compliance' },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-6 py-3 font-medium text-sm ${
                        activeTab === tab.id
                          ? 'border-b-2 border-primary-500 text-primary-600'
                          : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* Tab Content */}
                <div className="p-6">
                  {activeTab === 'summary' && <SummaryTab results={results} />}
                  {activeTab === 'extraction' && <ExtractionTab results={results} />}
                  {activeTab === 'anonymization' && (
                    <AnonymizationTab results={results} showFullText={showFullText} setShowFullText={setShowFullText} />
                  )}
                  {activeTab === 'compliance' && <ComplianceTab results={results} />}
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </>
  );
}

// Status Card Component
function StatusCard({ label, value, icon: Icon, color }) {
  const colorMap = {
    green: 'bg-green-50 text-green-700 border-green-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
  };

  return (
    <div className={`${colorMap[color] || colorMap.blue} rounded-lg p-4 border`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium opacity-75">{label}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
        </div>
        <Icon className="w-8 h-8 opacity-50" />
      </div>
    </div>
  );
}

// Summary Tab
function SummaryTab({ results }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Document Summary</h3>
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">
          {results?.summary || 'No summary available'}
        </p>
      </div>

      {results?.key_findings && results.key_findings.length > 0 && (
        <>
          <h3 className="text-lg font-semibold text-gray-900 mt-6">Key Findings</h3>
          <ul className="space-y-3">
            {results.key_findings.map((finding, idx) => (
              <li key={idx} className="flex items-start">
                <CheckCircle className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">{finding}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

// Extraction Tab
function ExtractionTab({ results }) {
  const ext = results?.extraction || {};
  
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600">Quality</p>
          <p className="text-xl font-semibold text-gray-900 mt-1">{ext.quality || 'N/A'}</p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600">Confidence</p>
          <p className="text-xl font-semibold text-gray-900 mt-1">{ext.confidence || 'N/A'}</p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600">Method</p>
          <p className="text-xl font-semibold text-gray-900 mt-1">{ext.method || 'N/A'}</p>
        </div>
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600">Pages</p>
          <p className="text-xl font-semibold text-gray-900 mt-1">{ext.pages || 'N/A'}</p>
        </div>
      </div>
    </div>
  );
}

// Anonymization Tab
function AnonymizationTab({ results, showFullText, setShowFullText }) {
  const anon = results?.anonymization || {};
  const piiStats = results?.pii_stats || {};
  
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Anonymity Metrics</h3>
        <div className="grid grid-cols-3 gap-4">
          <MetricCard
            label="K-Anonymity"
            value={anon.k_anonymity || 0}
            description="Indistinguishability level"
          />
          <MetricCard
            label="L-Diversity"
            value={anon.l_diversity || 0}
            description="Diversity of sensitive values"
          />
          <MetricCard
            label="T-Closeness"
            value={anon.t_closeness || 0}
            description="Closeness to distribution"
          />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">PII Detected</h3>
        {Object.keys(piiStats).length > 0 ? (
          <div className="space-y-2">
            {Object.entries(piiStats).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between bg-orange-50 p-3 rounded-lg border border-orange-200">
                <span className="font-medium text-gray-900">{type}</span>
                <span className="bg-orange-200 text-orange-900 px-3 py-1 rounded-full text-sm font-semibold">
                  {count}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 italic">No PII detected</p>
        )}
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Anonymized Text Preview</h3>
          <button
            onClick={() => setShowFullText(!showFullText)}
            className="flex items-center text-primary-600 hover:text-primary-700"
          >
            {showFullText ? (
              <>
                <EyeOff className="w-4 h-4 mr-2" />
                Hide
              </>
            ) : (
              <>
                <Eye className="w-4 h-4 mr-2" />
                Show Full
              </>
            )}
          </button>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 max-h-96 overflow-y-auto">
          <p className="text-gray-800 whitespace-pre-wrap text-sm">
            {showFullText
              ? anon.anonymized_text || 'N/A'
              : ((anon.anonymized_text || 'N/A').substring(0, 500) + '...')}
          </p>
        </div>
      </div>
    </div>
  );
}

// Compliance Tab
function ComplianceTab({ results }) {
  const comp = results?.compliance || {};
  const overallScore = Math.round(comp.overall_score || 0);
  
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Overall Compliance</h3>
        <div className="flex items-center space-x-6">
          <div className={`rounded-full w-32 h-32 flex items-center justify-center ${
            comp.is_compliant ? 'bg-green-100' : 'bg-red-100'
          }`}>
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-900">{overallScore}%</p>
              <p className="text-sm text-gray-600 mt-1">Score</p>
            </div>
          </div>
          <div className="flex-1">
            <p className="text-lg font-semibold">
              Status: <span className={comp.is_compliant ? 'text-green-600' : 'text-red-600'}>
                {comp.is_compliant ? '✓ Compliant' : '✗ Non-Compliant'}
              </span>
            </p>
            <p className="text-gray-600 mt-2">{comp.status || 'N/A'}</p>
          </div>
        </div>
      </div>

      {comp.framework_compliance && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Framework Details</h3>
          <div className="space-y-3">
            {Object.entries(comp.framework_compliance || {}).map(([framework, score]) => (
              <FrameworkScore
                key={framework}
                framework={framework}
                score={score}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Metric Card
function MetricCard({ label, value, description }) {
  return (
    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
      <p className="text-sm text-blue-600 font-medium">{label}</p>
      <p className="text-3xl font-bold text-blue-900 mt-2">{value}</p>
      <p className="text-xs text-blue-600 mt-2 opacity-75">{description}</p>
    </div>
  );
}

// Framework Score
function FrameworkScore({ framework, score }) {
  const scoreNum = Math.round(score * 100) || 0;
  
  return (
    <div className="flex items-center justify-between bg-gray-50 p-4 rounded-lg border border-gray-200">
      <span className="font-medium text-gray-900 capitalize">{framework}</span>
      <div className="flex items-center space-x-3">
        <div className="w-40 bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${
              scoreNum >= 70 ? 'bg-green-600' : scoreNum >= 40 ? 'bg-yellow-600' : 'bg-red-600'
            }`}
            style={{ width: `${scoreNum}%` }}
          />
        </div>
        <span className="text-sm font-semibold text-gray-900 w-12 text-right">{scoreNum}%</span>
      </div>
    </div>
  );
}

// Processing Progress Bar
function ProcessingProgressBar({ stage }) {
  const stages = [
    { id: 'queued', label: 'Queued' },
    { id: 'extracting', label: 'Extracting' },
    { id: 'anonymizing', label: 'Anonymizing' },
    { id: 'summarizing', label: 'Summarizing' },
    { id: 'validating', label: 'Validating' },
    { id: 'completed', label: 'Completed' },
  ];
  
  const currentIndex = stages.findIndex(s => s.id === stage);
  
  return (
    <div>
      <div className="flex justify-between items-center">
        {stages.map((s, idx) => (
          <div key={s.id} className="flex flex-col items-center flex-1">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
              idx <= currentIndex ? 'bg-primary-500 text-white' : 'bg-gray-300 text-gray-600'
            }`}>
              {idx < currentIndex ? '✓' : idx}
            </div>
            <p className="text-xs text-gray-600 mt-2 text-center">{s.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
