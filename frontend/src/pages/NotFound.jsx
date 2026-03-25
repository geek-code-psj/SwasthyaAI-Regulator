import React from 'react';
import { Helmet } from 'react-helmet-async';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, Home, ArrowRight } from 'lucide-react';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <>
      <Helmet>
        <title>Page Not Found - SwasthyaAI Regulator</title>
      </Helmet>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          {/* 404 Icon */}
          <div className="mb-8">
            <AlertCircle className="w-24 h-24 mx-auto text-red-500" />
          </div>

          {/* Error Code */}
          <h1 className="text-6xl font-bold text-gray-900 mb-2">404</h1>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Page Not Found</h2>

          {/* Description */}
          <p className="text-gray-600 mb-8 leading-relaxed">
            The page you're looking for doesn't exist or has been moved. It might have been
            deleted, or the URL might be incorrect.
          </p>

          {/* Helpful Suggestions */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h3 className="font-semibold text-gray-900 mb-4">Suggestions:</h3>
            <ul className="text-left space-y-2 text-gray-700 text-sm">
              <li className="flex items-start space-x-2">
                <ArrowRight className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                <span>Check the URL for typos or incorrect links</span>
              </li>
              <li className="flex items-start space-x-2">
                <ArrowRight className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                <span>Return to the dashboard to navigate properly</span>
              </li>
              <li className="flex items-start space-x-2">
                <ArrowRight className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                <span>Contact support if you believe this is an error</span>
              </li>
            </ul>
          </div>

          {/* Action Button */}
          <button
            onClick={() => navigate('/')}
            className="btn-primary inline-flex items-center space-x-2 px-6 py-3"
          >
            <Home className="w-5 h-5" />
            <span>Go to Dashboard</span>
          </button>

          {/* SwasthyaAI Branding */}
          <div className="mt-12 pt-8 border-t border-gray-300">
            <p className="text-sm text-gray-600">SwasthyaAI Regulator</p>
            <p className="text-xs text-gray-500 mt-1">Government Regulatory Compliance Platform</p>
          </div>
        </div>
      </div>
    </>
  );
}
