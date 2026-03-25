import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiMail, FiLock, FiLoader } from 'react-icons/fi';
import { authAPI } from '../services/api';

export default function Login() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  // Check if already logged in
  useEffect(() => {
    if (localStorage.getItem('access_token')) {
      navigate('/dashboard');
    }
  }, [navigate]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await authAPI.getToken();
      const { access_token } = response.data;

      // Store token
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify({
        id: 'test_user',
        username: 'Demo User',
        email: 'demo@swastya.ai',
        role: 'admin',
      }));

      setSuccess('Login successful! Redirecting...');
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-600 to-primary-800 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-block bg-white rounded-full p-4 mb-4">
            <h1 className="text-3xl font-bold text-primary-600">⚕️</h1>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">SwasthyaAI</h1>
          <p className="text-primary-100 text-lg">Regulatory Document Processing</p>
        </div>

        {/* Login Card */}
        <div className="card p-8 shadow-2xl">
          <h2 className="text-2xl font-bold mb-6 text-gray-900">Sign In</h2>

          {error && (
            <div className="alert alert-danger mb-4 flex items-center gap-3">
              <span className="text-lg">⚠️</span>
              {error}
            </div>
          )}

          {success && (
            <div className="alert alert-success mb-4 flex items-center gap-3">
              <span className="text-lg">✓</span>
              {success}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            {/* Demo Login Info */}
            <div className="bg-blue-50 border border-blue-300 rounded-lg p-4 mb-6">
              <p className="text-sm text-blue-900">
                <strong>Demo Mode:</strong> Click "Sign In" to access with demo credentials.
              </p>
            </div>

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="label">
                Email Address
              </label>
              <div className="relative">
                <FiMail className="absolute left-3 top-3 text-gray-400 text-lg" />
                <input
                  type="email"
                  id="email"
                  className="input pl-10"
                  placeholder="demo@swastya.ai"
                  disabled={loading}
                  defaultValue="demo@swastya.ai"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <div className="relative">
                <FiLock className="absolute left-3 top-3 text-gray-400 text-lg" />
                <input
                  type="password"
                  id="password"
                  className="input pl-10"
                  placeholder="••••••••"
                  disabled={loading}
                  defaultValue="demo"
                />
              </div>
            </div>

            {/* Sign In Button */}
            <button
              type="submit"
              disabled={loading}
              className="btn-primary lg w-full mt-6 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <FiLoader className="animate-spin" />
                  Signing In...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-center text-sm text-gray-600">
              SwasthyaAI Regulator v1.0 | CDSCO-IndiaAI Health Innovation Acceleration
            </p>
            <p className="text-center text-xs text-gray-500 mt-2">
              Healthcare Regulatory Document Processing System
            </p>
          </div>
        </div>

        {/* Info */}
        <div className="mt-8 bg-white bg-opacity-10 rounded-lg p-4 text-white text-sm">
          <p className="mb-3">
            <strong>Features:</strong>
          </p>
          <ul className="space-y-1 text-primary-100">
            <li>✓ AI-powered Document Processing</li>
            <li>✓ DPDP-Compliant Anonymization</li>
            <li>✓ Multi-Framework Compliance Validation</li>
            <li>✓ Executive Summarization</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
