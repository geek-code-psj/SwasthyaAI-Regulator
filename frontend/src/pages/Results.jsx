import React, { useState, useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  Download,
  FileText,
  BarChart3,
  Shield,
  CheckCircle,
  AlertCircle,
  ArrowLeft,
  Loader,
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
  const [activeTab, setActiveTab] = useState('summary');
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    fetchStatus();
    const pollInterval = setInterval(() => {
      fetchStatus();
    }, 2000);
    return () => clearInterval(pollInterval);
  }, [id]);

  useEffect(() => {
    if ((status?.status === 'completed' || status?.status === 'failed') && !results) {
      fetchResults();
    }
  }, [status?.status]);

  const fetchStatus = async () => {
    try {
      const res = await submissionAPI.getStatus(id);
      setStatus(res.data);
      setLoading(false);

      // Fetch results immediately if already completed or failed
      if ((res.data.status === 'completed' || res.data.status === 'failed') && !results) {
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
      element.download = `validation-report-${id}-${Date.now()}.txt`;
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
SWASTHAAI REGULATOR - VALIDATION REPORT
========================================

SUBMISSION INFORMATION
---------------------
ID: ${results?.submission_id}
Filename: ${results?.filename}
Status: ${results?.status}
Overall: ${results?.overall_status}

VALIDATION RESULTS
------------------
Total Checks: ${results?.total_checks}
Passed: ${results?.checks_passed}
Failed: ${results?.checks_failed}
Skipped: ${results?.checks_skipped}

FORM COMPLETENESS
-----------------
Score: ${Math.round(results?.form_completeness || 0)}%

KEY FINDINGS
-----------
${(results?.key_findings || []).map((f, i) => `${i + 1}. ${f}`).join('\n')}

DETAILED FINDINGS
-----------------
${(results?.findings || []).join('\n')}

RECOMMENDATIONS
----------------
${(results?.recommendations || []).join('\n')}

COMPREHENSIVE SUMMARY
---------------------
${results?.summary || 'No summary available'}

Generated: ${new Date().toLocaleString()}
`;
  };

  if (loading) {
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

  // Wait for both status and results
  if (!status || !results) {
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
                  <h2 className="text-2xl font-bold mb-4">Loading Results</h2>
                  <p className="text-gray-600 mb-4">
                    Status: <span className="font-semibold capitalize">{status?.status || 'processing'}</span>
                  </p>
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
                    <h1 className="text-3xl font-bold text-gray-900">{results?.filename}</h1>
                    <p className="text-sm text-gray-500 mt-1">ID: {id}</p>
                  </div>
                </div>
                <button
                  onClick={downloadResults}
                  className="btn btn-primary"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download Report
                </button>
              </div>

              {/* Status Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <StatusCard
                  label="Overall Status"
                  value={results?.overall_status === 'PASS' ? 'APPROVED' : 'FAILED'}
                  icon={results?.overall_status === 'PASS' ? CheckCircle : AlertCircle}
                  color={results?.overall_status === 'PASS' ? 'green' : 'red'}
                />
                <StatusCard
                  label="Checks Passed"
                  value={results?.checks_passed || 0}
                  icon={CheckCircle}
                  color="green"
                />
                <StatusCard
                  label="Form Completeness"
                  value={`${Math.round(results?.form_completeness || 0)}%`}
                  icon={TrendingUp}
                  color={results?.form_completeness >= 70 ? 'green' : 'orange'}
                />
                <StatusCard
                  label="Total Checks"
                  value={results?.total_checks || 0}
                  icon={BarChart3}
                  color="blue"
                />
              </div>

              {/* Tabs */}
              <div className="card mb-6">
                <div className="flex border-b border-gray-200">
                  {[
                    { id: 'summary', label: 'Summary' },
                    { id: 'validation', label: 'Validation Results' },
                    { id: 'findings', label: 'Findings & Recommendations' },
                    { id: 'details', label: 'Details' },
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
                  {activeTab === 'validation' && <ValidationTab results={results} />}
                  {activeTab === 'findings' && <FindingsTab results={results} />}
                  {activeTab === 'details' && <DetailsTab results={results} />}
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </>
  );
}

// Summary Tab - Shows comprehensive summary
function SummaryTab({ results }) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Overall Assessment</h3>
        <div className={`rounded-lg p-6 border-2 ${
          results?.overall_status === 'PASS'
            ? 'bg-green-50 border-green-200'
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-center space-x-4">
            {results?.overall_status === 'PASS' ? (
              <CheckCircle className="w-12 h-12 text-green-600" />
            ) : (
              <AlertCircle className="w-12 h-12 text-red-600" />
            )}
            <div>
              <p className={`text-xl font-bold ${
                results?.overall_status === 'PASS' ? 'text-green-900' : 'text-red-900'
              }`}>
                {results?.overall_status === 'PASS'
                  ? 'APPROVED FOR REGULATORY REVIEW'
                  : 'REQUIRES ATTENTION'}
              </p>
              {results?.form_completeness && (
                <p className="text-sm text-gray-600 mt-1">
                  Form Completeness: {Math.round(results.form_completeness)}%
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Validation Pipeline Summary</h3>
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <p className="text-sm text-green-600 font-semibold">Passed</p>
            <p className="text-2xl font-bold text-green-900">{results?.checks_passed || 0}</p>
          </div>
          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
            <p className="text-sm text-red-600 font-semibold">Failed</p>
            <p className="text-2xl font-bold text-red-900">{results?.checks_failed || 0}</p>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
            <p className="text-sm text-yellow-600 font-semibold">Skipped</p>
            <p className="text-2xl font-bold text-yellow-900">{results?.checks_skipped || 0}</p>
          </div>
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <p className="text-sm text-blue-600 font-semibold">Total Checks</p>
            <p className="text-2xl font-bold text-blue-900">{results?.total_checks || 0}</p>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Comprehensive Summary</h3>
        <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
          <p className="text-gray-800 whitespace-pre-wrap font-mono text-sm leading-relaxed">
            {results?.summary || 'No summary available'}
          </p>
        </div>
      </div>

      {results?.key_findings && results.key_findings.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Findings</h3>
          <ul className="space-y-3">
            {results.key_findings.map((finding, idx) => (
              <li key={idx} className="flex items-start">
                <CheckCircle className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700">{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// Validation Results Tab
function ValidationTab({ results }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Validation Checks</h3>
      {results?.validation_results && results.validation_results.length > 0 ? (
        results.validation_results.map((check, idx) => (
          <div
            key={idx}
            className={`rounded-lg p-4 border-2 ${
              check.status === 'PASS'
                ? 'bg-green-50 border-green-200'
                : check.status === 'FAIL'
                ? 'bg-red-50 border-red-200'
                : check.status === 'SKIPPED'
                ? 'bg-yellow-50 border-yellow-200'
                : 'bg-gray-50 border-gray-200'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  {check.status === 'PASS' && (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  )}
                  {check.status === 'FAIL' && (
                    <AlertCircle className="w-5 h-5 text-red-600" />
                  )}
                  {check.status === 'SKIPPED' && (
                    <span className="text-xl">⊘</span>
                  )}
                  <h4 className="font-semibold text-gray-900">{check.check_type}</h4>
                </div>
                <p className={`text-sm mt-2 ${
                  check.status === 'PASS'
                    ? 'text-green-700'
                    : check.status === 'FAIL'
                    ? 'text-red-700'
                    : 'text-gray-700'
                }`}>
                  {check.details?.reason || `Status: ${check.status}`}
                </p>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                check.status === 'PASS'
                  ? 'bg-green-200 text-green-800'
                  : check.status === 'FAIL'
                  ? 'bg-red-200 text-red-800'
                  : 'bg-yellow-200 text-yellow-800'
              }`}>
                {check.status}
              </span>
            </div>
            {check.details?.completeness && (
              <div className="mt-3 pt-3 border-t border-gray-300">
                <p className="text-sm text-gray-600">
                  Completeness: <span className="font-semibold">{Math.round(check.details.completeness)}%</span>
                </p>
              </div>
            )}
          </div>
        ))
      ) : (
        <p className="text-gray-500 italic">No validation results available</p>
      )}
    </div>
  );
}

// Findings & Recommendations Tab
function FindingsTab({ results }) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Detailed Findings</h3>
        <div className="space-y-3">
          {results?.findings && results.findings.length > 0 ? (
            results.findings.map((finding, idx) => (
              <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-gray-800 text-sm">{finding}</p>
              </div>
            ))
          ) : (
            <p className="text-gray-500 italic">No findings available</p>
          )}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
        <div className="space-y-3">
          {results?.recommendations && results.recommendations.length > 0 ? (
            results.recommendations.map((rec, idx) => (
              <div
                key={idx}
                className={`rounded-lg p-4 border-l-4 ${
                  rec.includes('✓')
                    ? 'bg-green-50 border-l-green-500'
                    : rec.includes('✗')
                    ? 'bg-red-50 border-l-red-500'
                    : rec.includes('⚠')
                    ? 'bg-yellow-50 border-l-yellow-500'
                    : 'bg-blue-50 border-l-blue-500'
                }`}
              >
                <p className="text-gray-800 text-sm">{rec}</p>
              </div>
            ))
          ) : (
            <p className="text-gray-500 italic">No recommendations</p>
          )}
        </div>
      </div>
    </div>
  );
}

// Details Tab
function DetailsTab({ results }) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Submission Details</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <p className="text-xs text-gray-600 uppercase font-semibold">Submission ID</p>
            <p className="font-mono text-sm text-gray-900 mt-1 break-all">{results?.submission_id}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <p className="text-xs text-gray-600 uppercase font-semibold">Filename</p>
            <p className="font-medium text-gray-900 mt-1">{results?.filename}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <p className="text-xs text-gray-600 uppercase font-semibold">Status</p>
            <p className="font-medium text-gray-900 mt-1 capitalize">{results?.status}</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <p className="text-xs text-gray-600 uppercase font-semibold">Form Completeness</p>
            <p className="font-medium text-gray-900 mt-1">{Math.round(results?.form_completeness || 0)}%</p>
          </div>
        </div>
      </div>

      {results?.critical_issues && results.critical_issues.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Critical Issues</h3>
          <div className="space-y-2">
            {results.critical_issues.map((issue, idx) => (
              <div key={idx} className="bg-red-50 border-l-4 border-l-red-500 p-4 rounded">
                <p className="text-red-800 text-sm">{issue}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Timestamp</h3>
        <p className="text-gray-600 text-sm">
          {results?.timestamp ? new Date(results.timestamp).toLocaleString() : 'N/A'}
        </p>
      </div>
    </div>
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
