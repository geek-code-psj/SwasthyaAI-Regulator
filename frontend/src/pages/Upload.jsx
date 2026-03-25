import React, { useState, useRef } from 'react';
import { Helmet } from 'react-helmet-async';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Upload, FileText, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';

import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import { submissionAPI } from '../services/api';
import { useSubmissionStore } from '../stores';

export default function UploadPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [file, setFile] = useState(null);
  const [documentType, setDocumentType] = useState('form_44');
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errors, setErrors] = useState([]);

  const { addSubmission } = useSubmissionStore();

  const documentTypes = [
    { value: 'form_44', label: 'Form 44 - Drug Dossier', description: 'Pharmaceutical dossier' },
    { value: 'form_md26', label: 'Form MD-26 - Medical Device', description: 'Medical device submission' },
    { value: 'drug_dossier', label: 'Clinical Trial Dossier', description: 'Clinical research data' },
  ];

  const validateFile = (selectedFile) => {
    const errors = [];
    const maxSize = 100 * 1024 * 1024; // 100MB
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff'];

    if (!selectedFile) {
      errors.push('Please select a file');
    } else if (selectedFile.size > maxSize) {
      errors.push(`File size must be less than 100MB (Current: ${(selectedFile.size / 1024 / 1024).toFixed(2)}MB)`);
    } else if (!allowedTypes.includes(selectedFile.type)) {
      errors.push('File must be PDF, JPEG, PNG, or TIFF format');
    }

    return errors;
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    const validationErrors = validateFile(selectedFile);
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      setFile(null);
    } else {
      setErrors([]);
      setFile(selectedFile);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      const validationErrors = validateFile(droppedFile);
      if (validationErrors.length > 0) {
        setErrors(validationErrors);
        setFile(null);
      } else {
        setErrors([]);
        setFile(droppedFile);
      }
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();

    if (!file) {
      toast.error('Please select a file');
      return;
    }

    setLoading(true);
    setUploadProgress(0);

    try {
      const response = await submissionAPI.uploadFile(file, documentType);
      const { submission_id, status, message } = response.data;

      addSubmission({
        id: submission_id,
        filename: file.name,
        status,
        created_at: new Date().toISOString(),
        submission_type: documentType,
      });

      toast.success(message);
      setFile(null);

      // Redirect to processing status
      setTimeout(() => {
        navigate(`/submission/${submission_id}/status`);
      }, 1500);
    } catch (error) {
      const errorMsg =
        error.response?.data?.error ||
        error.message ||
        'Failed to upload file. Please try again.';
      toast.error(errorMsg);
      setErrors([errorMsg]);
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  return (
    <>
      <Helmet>
        <title>Upload Document - SwasthyaAI Regulator</title>
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
                <h2 className="text-3xl font-bold text-gray-900">Upload Document</h2>
                <p className="text-gray-600 mt-2">
                  Upload regulatory documents for AI-powered processing and compliance validation
                </p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Upload Form */}
                <div className="lg:col-span-2">
                  <form onSubmit={handleUpload} className="space-y-6">
                    {/* File Upload Area */}
                    <div
                      onDragOver={handleDragOver}
                      onDrop={handleDrop}
                      className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center hover:border-blue-400 hover:bg-blue-50 transition-colors cursor-pointer"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-lg font-semibold text-gray-900 mb-2">
                        Drag and drop your document here
                      </p>
                      <p className="text-sm text-gray-600 mb-4">or click to select</p>
                      <input
                        ref={fileInputRef}
                        type="file"
                        onChange={handleFileSelect}
                        accept=".pdf,.jpg,.jpeg,.png,.tiff,.tif"
                        className="hidden"
                        disabled={loading}
                      />
                      <p className="text-xs text-gray-500">
                        Supported: PDF, JPEG, PNG, TIFF (Max 100MB)
                      </p>
                    </div>

                    {/* Selected File */}
                    {file && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center space-x-4">
                        <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
                        <div className="flex-1">
                          <p className="font-medium text-green-900">{file.name}</p>
                          <p className="text-sm text-green-700">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            setFile(null);
                            setErrors([]);
                          }}
                          className="text-green-600 hover:text-green-700 font-medium"
                        >
                          Change
                        </button>
                      </div>
                    )}

                    {/* Errors */}
                    {errors.length > 0 && (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div className="flex items-start space-x-3">
                          <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                          <div>
                            <h3 className="font-semibold text-red-900">Validation Errors</h3>
                            <ul className="mt-2 space-y-1">
                              {errors.map((error, idx) => (
                                <li key={idx} className="text-sm text-red-700">
                                  • {error}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Document Type Selection */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-900 mb-3">
                        Document Type
                      </label>
                      <div className="space-y-2">
                        {documentTypes.map((type) => (
                          <label
                            key={type.value}
                            className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 cursor-pointer transition-colors"
                          >
                            <input
                              type="radio"
                              name="documentType"
                              value={type.value}
                              checked={documentType === type.value}
                              onChange={(e) => setDocumentType(e.target.value)}
                              className="w-4 h-4 text-blue-600"
                            />
                            <div className="ml-4">
                              <p className="font-medium text-gray-900">{type.label}</p>
                              <p className="text-sm text-gray-600">{type.description}</p>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Upload Progress */}
                    {loading && uploadProgress > 0 && (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm font-medium text-gray-900">Uploading...</p>
                          <p className="text-sm font-medium text-gray-600">{uploadProgress}%</p>
                        </div>
                        <div className="progress-bar">
                          <div
                            className="progress-fill"
                            style={{ width: `${uploadProgress}%` }}
                          ></div>
                        </div>
                      </div>
                    )}

                    {/* Submit Buttons */}
                    <div className="flex space-x-4">
                      <button
                        type="submit"
                        disabled={!file || loading}
                        className="btn-primary flex-1 flex items-center justify-center space-x-2"
                      >
                        {loading ? (
                          <>
                            <span className="inline-block animate-spin">⏳</span>
                            <span>Processing...</span>
                          </>
                        ) : (
                          <>
                            <Upload className="w-5 h-5" />
                            <span>Upload & Process</span>
                          </>
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={() => navigate('/')}
                        className="btn-secondary"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>

                {/* Sidebar Info */}
                <div className="space-y-4">
                  {/* Processing Stages */}
                  <div className="card">
                    <div className="card-header">
                      <h3 className="font-semibold text-gray-900">Processing Pipeline</h3>
                    </div>
                    <div className="card-body space-y-4">
                      {[
                        { step: 1, title: 'OCR Extraction', desc: 'Text from documents' },
                        { step: 2, title: 'Anonymization', desc: 'Remove PII data' },
                        { step: 3, title: 'Summarization', desc: 'Generate summary' },
                        { step: 4, title: 'Compliance Check', desc: '4 frameworks' },
                      ].map((item) => (
                        <div key={item.step} className="flex items-start space-x-3">
                          <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold flex items-center justify-center text-sm">
                            {item.step}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 text-sm">{item.title}</p>
                            <p className="text-xs text-gray-600">{item.desc}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Key Features */}
                  <div className="card bg-blue-50 border border-blue-200">
                    <div className="card-body">
                      <h3 className="font-semibold text-blue-900 mb-3">Key Features</h3>
                      <ul className="space-y-2 text-sm text-blue-800">
                        <li>✓ DPDP-compliant anonymization</li>
                        <li>✓ AI-powered summarization</li>
                        <li>✓ Multi-framework compliance</li>
                        <li>✓ Encrypted audit trails</li>
                        <li>✓ Real-time processing status</li>
                      </ul>
                    </div>
                  </div>

                  {/* File Limits */}
                  <div className="card bg-yellow-50 border border-yellow-200">
                    <div className="card-body">
                      <h3 className="font-semibold text-yellow-900 mb-2">File Requirements</h3>
                      <ul className="space-y-1 text-xs text-yellow-800">
                        <li>• Max size: <strong>100MB</strong></li>
                        <li>• Formats: <strong>PDF, JPEG, PNG, TIFF</strong></li>
                        <li>• Processing time: <strong>20-30s</strong></li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </>
  );
}
