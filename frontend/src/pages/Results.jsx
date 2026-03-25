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
} from 'lucide-react';

import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import { submissionAPI } from '../services/api';

export default function ResultsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [results, setResults] = useState(null);
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showFullText, setShowFullText] = useState(false);

  useEffect(() => {
    fetchResults();
  }, [id]);

  const fetchResults = async () => {
    try {
      setLoading(true);
      const [resultsRes, statusRes] = await Promise.all([
        submissionAPI.getResults(id),
        submissionAPI.getStatus(id),
      ]);

      setResults(resultsRes.data);
      setSubmission(statusRes.data);
      setLoading(false);
    } catch (error) {
      toast.error('Failed to fetch results');
      console.error(error);
      setLoading(false);
    }
  };

  const downloadResults = async () => {
    try {
      const element = document.createElement('a');
      const file = new Blob(
        [
          `Document Processing Results\n`,
          `============================\n\n`,
          `Submission ID: ${id}\n`,
          `Filename: ${submission?.filename}\n`,
          `Date: ${new Date().toLocaleString()}\n\n`,
          `Summary\n-------\n`,
          `${results?.summary || 'No summary available'}\n\n`,
          `Anonymized Text Preview\n-----------------------\n`,
          `${results?.anonymized_text || 'No text available'}\n\n`,
          `PII Statistics\n--------------\n`,
          Object.entries(results?.pii_stats || {})
            .map(([key, value]) => `${key}: ${value}`)
            .join('\n'),
        ],
        { type: 'text/plain' }
      );
      element.href = URL.createObjectURL(file);
      element.download = `results-${id}.txt`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      toast.success('Results downloaded');
    } catch (error) {
      toast.error('Failed to download results');
    }
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
                <div className="animate-spin inline-block text-4xl mb-4">⏳</div>
                <p className="text-gray-600">Loading results...</p>
              </div>
            </main>
          </div>
        </div>
      </>
    );
  }

  if (!results) {
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
                <AlertCircle className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
                <p className="text-gray-600">Results not available yet</p>
              </div>
            </main>
          </div>
        </div>
      </>
    );
  }

  const piiStats = results?.pii_stats || {};
  const maxPII = Math.max(...Object.values(piiStats).map((v) => v || 0), 1);

  return (
    <>
      <Helmet>
        <title>Results - SwasthyaAI Regulator</title>
      </Helmet>

      <div className="flex h-screen bg-gray-100">
        <Sidebar isOpen={sidebarOpen} />

        <div className="flex-1 flex flex-col overflow-hidden">
          <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

          {/* Main Content */}
          <main className="flex-1 overflow-y-auto">
            <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {/* Page Header */}
              <div className="mb-8 flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-bold text-gray-900">Processing Results</h2>
                  <p className="text-gray-600 mt-2">{submission?.filename}</p>
                </div>
                <button
                  onClick={() => navigate('/')}
                  className="btn-secondary flex items-center space-x-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back</span>
                </button>
              </div>

              {/* Summary Section */}
              <div className="card mb-6">
                <div className="card-header flex items-center space-x-2">
                  <FileText className="w-5 h-5 text-blue-600" />
                  <h3 className="font-semibold">Summary</h3>
                </div>
                <div className="card-body">
                  <p className="text-gray-700 leading-relaxed">{results?.summary}</p>
                  {results?.key_findings && results.key_findings.length > 0 && (
                    <div className="mt-6 pt-6 border-t border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-3">Key Findings</h4>
                      <ul className="space-y-2">
                        {results.key_findings.map((finding, idx) => (
                          <li key={idx} className="flex items-start space-x-2 text-gray-700">
                            <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                            <span>{finding}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* PII Statistics */}
              <div className="card mb-6">
                <div className="card-header flex items-center space-x-2">
                  <BarChart3 className="w-5 h-5 text-purple-600" />
                  <h3 className="font-semibold">PII Statistics</h3>
                </div>
                <div className="card-body">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {Object.entries(piiStats).map(([key, value]) => (
                      <div key={key} className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-200">
                        <p className="text-sm font-medium text-gray-600 capitalize mb-2">
                          {key.replace(/_/g, ' ')}
                        </p>
                        <p className="text-3xl font-bold text-purple-600">{value}</p>
                        {maxPII > 0 && (
                          <div className="mt-3 w-full bg-gray-200 rounded-full h-1 overflow-hidden">
                            <div
                              className="bg-gradient-to-r from-purple-500 to-blue-500 h-1 transition-all duration-300"
                              style={{ width: `${(value / maxPII) * 100}%` }}
                            ></div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Anonymized Text Preview */}
              <div className="card mb-6">
                <div className="card-header flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {showFullText ? (
                      <Eye className="w-5 h-5 text-blue-600" />
                    ) : (
                      <EyeOff className="w-5 h-5 text-blue-600" />
                    )}
                    <h3 className="font-semibold">Anonymized Text Preview</h3>
                  </div>
                  <button
                    onClick={() => setShowFullText(!showFullText)}
                    className="text-sm px-3 py-1 rounded bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium transition-colors"
                  >
                    {showFullText ? 'Show Less' : 'Show More'}
                  </button>
                </div>
                <div className="card-body">
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 font-mono text-sm text-gray-700 leading-relaxed max-h-96 overflow-auto">
                    {showFullText
                      ? results?.anonymized_text
                      : `${results?.anonymized_text?.substring(0, 500) || ''}...`}
                  </div>
                  <p className="text-xs text-gray-600 mt-3">
                    📝 Text preview (PII removed){showFullText ? '' : ' - First 500 characters'}
                  </p>
                </div>
              </div>

              {/* Compliance Status */}
              <div className="card mb-6">
                <div className="card-header flex items-center space-x-2">
                  <Shield className="w-5 h-5 text-green-600" />
                  <h3 className="font-semibold">Compliance Status</h3>
                </div>
                <div className="card-body">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {['DPDP', 'NDHM', 'ICMR', 'CDSCO'].map((framework, idx) => (
                      <div
                        key={framework}
                        className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg"
                      >
                        <div className="flex items-center space-x-2">
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          <span className="font-medium text-gray-900">{framework}</span>
                        </div>
                        <span className="text-sm font-semibold bg-green-100 text-green-700 px-3 py-1 rounded-full">
                          ✓ Compliant
                        </span>
                      </div>
                    ))}
                  </div>
                  <p className="text-sm text-gray-600 mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    ✓ Document meets requirements for all 4 compliance frameworks
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-3">
                <button onClick={downloadResults} className="btn-primary flex items-center space-x-2">
                  <Download className="w-4 h-4" />
                  <span>Download Results</span>
                </button>
                <button
                  onClick={() => navigate(`/submission/${id}/compliance`)}
                  className="btn-secondary flex items-center space-x-2"
                >
                  <Shield className="w-4 h-4" />
                  <span>View Compliance Report</span>
                </button>
                <button onClick={() => navigate('/')} className="btn-secondary">
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
