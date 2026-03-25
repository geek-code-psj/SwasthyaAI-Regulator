import { useState } from 'react';
import { FiUpload, FiFile, FiX, FiLoader } from 'react-icons/fi';
import { submissionAPI } from '../services/api';

export default function Upload({ onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [docType, setDocType] = useState('form_44');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      validateAndSetFile(files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile) => {
    const maxSize = 100 * 1024 * 1024; // 100MB
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff'];

    if (!allowedTypes.includes(selectedFile.type)) {
      setError('Invalid file type. Please upload PDF or image files.');
      setFile(null);
      return;
    }

    if (selectedFile.size > maxSize) {
      setError('File size exceeds 100MB limit.');
      setFile(null);
      return;
    }

    setError('');
    setFile(selectedFile);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await submissionAPI.uploadFile(file, docType);
      const { submission_id, message, async_mode } = response.data;

      if (async_mode) {
        setSuccess(`${message}\nRedirecting to results...`);
      } else {
        setSuccess(`${message}\nRedirecting to results...`);
      }
      
      setFile(null);

      // Reset form
      document.querySelector('input[type="file"]').value = '';
      setDocType('form_44');

      // Redirect to results page after 1.5 seconds
      setTimeout(() => {
        if (onUploadSuccess) {
          onUploadSuccess(submission_id);
        }
        window.location.href = `/results/${submission_id}`;
      }, 1500);
      
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-8">
      <h2 className="text-2xl font-bold mb-2">Upload Document</h2>
      <p className="text-gray-600 mb-6">Upload regulatory documents for processing</p>

      <form onSubmit={handleUpload} className="space-y-6">
        {/* Document Type */}
        <div>
          <label htmlFor="docType" className="label">
            Document Type
          </label>
          <select
            id="docType"
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="input"
            disabled={loading}
          >
            <option value="form_44">Form 44 - Drug Dossier</option>
            <option value="form_md26">Form MD-26 - Medical Device</option>
            <option value="drug_dossier">Drug Dossier</option>
          </select>
        </div>

        {/* Drag and Drop Area */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 bg-gray-50 hover:border-primary-400'
          } ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="fileInput"
            className="hidden"
            onChange={handleFileChange}
            accept=".pdf,.jpg,.jpeg,.png,.tif,.tiff"
            disabled={loading}
          />

          <label htmlFor="fileInput" className="cursor-pointer">
            <div className="mb-4">
              <FiUpload className="mx-auto text-4xl text-primary-500 mb-2" />
              <p className="text-lg font-medium text-gray-900">
                {dragActive ? 'Drop file here' : 'Drag and drop your document'}
              </p>
              <p className="text-sm text-gray-500 mt-1">or click to browse</p>
            </div>

            <p className="text-xs text-gray-500">
              Supported formats: PDF, JPG, PNG, TIFF | Max size: 100MB
            </p>
          </label>
        </div>

        {/* Selected File */}
        {file && (
          <div className="bg-blue-50 border border-blue-300 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FiFile className="text-blue-600 text-xl" />
              <div>
                <p className="font-medium text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-600">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                setFile(null);
                document.querySelector('input[type="file"]').value = '';
              }}
              className="text-red-600 hover:text-red-800"
              disabled={loading}
            >
              <FiX className="text-xl" />
            </button>
          </div>
        )}

        {/* Alerts */}
        {error && (
          <div className="alert alert-danger flex items-start gap-3">
            <span className="text-lg">⚠️</span>
            {error}
          </div>
        )}

        {success && (
          <div className="alert alert-success flex items-start gap-3">
            <span className="text-lg">✓</span>
            <div>
              <p className="font-medium">Document uploaded successfully!</p>
              <p className="text-sm mt-1">{success}</p>
            </div>
          </div>
        )}

        {/* Upload Button */}
        <button
          type="submit"
          disabled={!file || loading}
          className={`btn-primary lg w-full flex items-center justify-center gap-2 ${
            !file || loading ? 'btn-disabled' : ''
          }`}
        >
          {loading ? (
            <>
              <FiLoader className="animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <FiUpload />
              Upload Document
            </>
          )}
        </button>
      </form>
    </div>
  );
}
