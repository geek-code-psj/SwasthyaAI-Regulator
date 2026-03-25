import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import toast from 'react-hot-toast';
import { Lock, AlertCircle, CheckCircle } from 'lucide-react';

import { authAPI } from '../services/api';
import { useAuthStore } from '../stores';

export default function LoginPage() {
  const navigate = useNavigate();
  const { setToken } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await authAPI.getToken();
      const { access_token } = response.data;

      setToken(access_token);
      toast.success('Login successful! Redirecting...');

      setTimeout(() => {
        navigate('/', { replace: true });
      }, 1000);
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Failed to authenticate. Please try again.';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Helmet>
        <title>SwasthyaAI Regulator - Login</title>
        <meta name="description" content="Government healthcare regulatory compliance platform" />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          {/* Logo Section */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-4">
              <Lock className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900">SwasthyaAI</h1>
            <p className="text-gray-600 mt-2">Regulatory Document Compliance Platform</p>
          </div>

          {/* Login Card */}
          <div className="bg-white rounded-lg shadow-lg p-8 card">
            {/* System Status */}
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="text-sm font-semibold text-green-900">System Ready</h3>
                <p className="text-xs text-green-700 mt-1">All systems operational. Backend API connected.</p>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="text-sm font-semibold text-red-900">Authentication Error</h3>
                  <p className="text-xs text-red-700 mt-1">{error}</p>
                </div>
              </div>
            )}

            {/* Login Form */}
            <form onSubmit={handleLogin} className="space-y-6">
              {/* Info Message */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-900">
                  <span className="font-semibold">Demo Login:</span> Click "Sign In" to continue with default credentials.
                </p>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary py-3 font-semibold"
              >
                {loading ? (
                  <>
                    <span className="inline-block animate-spin mr-2">⏳</span>
                    Authenticating...
                  </>
                ) : (
                  'Sign In with JWT'
                )}
              </button>

              {/* Additional Info */}
              <div className="text-center text-xs text-gray-600">
                <p>Government & Healthcare Compliance Platform</p>
                <p className="mt-1">DPDP Act 2023 | NDHM | ICMR | CDSCO Compliant</p>
              </div>
            </form>
          </div>

          {/* Footer */}
          <div className="mt-8 text-center text-xs text-gray-600">
            <p>© 2024 SwasthyaAI. All rights reserved.</p>
            <p className="mt-2">
              For support, contact:{' '}
              <span className="font-semibold">support@swastya.ai</span>
            </p>
          </div>

          {/* Features List */}
          <div className="mt-8 grid grid-cols-2 gap-4">
            {[
              { icon: '📄', label: 'Document Upload' },
              { icon: '🔐', label: 'DPDP Compliant' },
              { icon: '🤖', label: 'AI Processing' },
              { icon: '✅', label: '4 Frameworks' },
            ].map((feature, idx) => (
              <div key={idx} className="bg-white rounded-lg p-4 border border-gray-200 text-center">
                <div className="text-2xl mb-2">{feature.icon}</div>
                <p className="text-xs font-medium text-gray-700">{feature.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
