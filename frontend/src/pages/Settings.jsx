import React, { useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  Settings as SettingsIcon,
  User,
  Lock,
  Bell,
  HardDrive,
  LogOut,
  Save,
  RotateCcw,
} from 'lucide-react';

import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import { useAuthStore } from '../stores';

export default function SettingsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  // Profile Settings
  const [profile, setProfile] = useState({
    name: 'Dr. Regulatory Officer',
    email: 'officer@swasthyai.gov',
    organization: 'Regulatory Department',
    role: 'Compliance Officer',
  });

  const [profileEditing, setProfileEditing] = useState(false);

  // Notification Settings
  const [notifications, setNotifications] = useState({
    emailOnCompletion: true,
    emailOnError: true,
    dailyDigest: false,
    newFeatures: true,
  });

  // Data Settings
  const [dataRetention, setDataRetention] = useState({
    retentionDays: 90,
    autoDeleteProcessed: false,
    backupEnabled: true,
  });

  const handleSaveProfile = () => {
    toast.success('Profile settings saved');
    setProfileEditing(false);
  };

  const handleSaveNotifications = () => {
    toast.success('Notification preferences updated');
  };

  const handleSaveDataSettings = () => {
    toast.success('Data settings saved');
  };

  const handleResetDefaults = () => {
    toast.success('Settings reset to defaults');
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    toast.success('Logged out successfully');
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Lock },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'data', label: 'Data', icon: HardDrive },
  ];

  return (
    <>
      <Helmet>
        <title>Settings - SwasthyaAI Regulator</title>
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
                <h2 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
                  <SettingsIcon className="w-8 h-8 text-blue-600" />
                  <span>Settings</span>
                </h2>
                <p className="text-gray-600 mt-2">Manage your account and preferences</p>
              </div>

              {/* Tab Navigation */}
              <div className="flex flex-wrap gap-2 mb-8 bg-white rounded-lg p-2 shadow-sm">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${
                        activeTab === tab.id
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* Profile Tab */}
              {activeTab === 'profile' && (
                <div className="space-y-6">
                  <div className="card">
                    <div className="card-header">
                      <h3 className="font-semibold flex items-center space-x-2">
                        <User className="w-5 h-5 text-blue-600" />
                        <span>Personal Information</span>
                      </h3>
                    </div>
                    <div className="card-body space-y-4">
                      {profileEditing ? (
                        <>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Full Name
                            </label>
                            <input
                              type="text"
                              value={profile.name}
                              onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                              className="input-field"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Email Address
                            </label>
                            <input
                              type="email"
                              value={profile.email}
                              onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                              className="input-field"
                              disabled
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Organization
                            </label>
                            <input
                              type="text"
                              value={profile.organization}
                              onChange={(e) =>
                                setProfile({ ...profile, organization: e.target.value })
                              }
                              className="input-field"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Role
                            </label>
                            <input
                              type="text"
                              value={profile.role}
                              onChange={(e) => setProfile({ ...profile, role: e.target.value })}
                              className="input-field"
                            />
                          </div>

                          <div className="flex gap-3 pt-4">
                            <button
                              onClick={handleSaveProfile}
                              className="btn-primary flex items-center space-x-2"
                            >
                              <Save className="w-4 h-4" />
                              <span>Save Changes</span>
                            </button>
                            <button
                              onClick={() => setProfileEditing(false)}
                              className="btn-secondary"
                            >
                              Cancel
                            </button>
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <p className="text-sm text-gray-600">Full Name</p>
                              <p className="font-semibold text-gray-900">{profile.name}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">Email</p>
                              <p className="font-semibold text-gray-900">{profile.email}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">Organization</p>
                              <p className="font-semibold text-gray-900">{profile.organization}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">Role</p>
                              <p className="font-semibold text-gray-900">{profile.role}</p>
                            </div>
                          </div>
                          <button
                            onClick={() => setProfileEditing(true)}
                            className="btn-secondary w-full"
                          >
                            Edit Profile
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Security Tab */}
              {activeTab === 'security' && (
                <div className="space-y-6">
                  <div className="card">
                    <div className="card-header">
                      <h3 className="font-semibold flex items-center space-x-2">
                        <Lock className="w-5 h-5 text-blue-600" />
                        <span>Security Settings</span>
                      </h3>
                    </div>
                    <div className="card-body space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Change Password
                        </label>
                        <button className="btn-secondary w-full">Update Password</button>
                      </div>

                      <div className="border-t pt-4">
                        <h4 className="font-semibold text-gray-900 mb-3">Two-Factor Authentication</h4>
                        <p className="text-sm text-gray-600 mb-4">
                          Add an extra layer of security to your account
                        </p>
                        <button className="btn-secondary w-full">Enable 2FA</button>
                      </div>

                      <div className="border-t pt-4">
                        <h4 className="font-semibold text-gray-900 mb-3">Active Sessions</h4>
                        <div className="bg-gray-50 rounded-lg p-3">
                          <p className="text-sm text-gray-700">
                            <strong>Current Session:</strong> Windows • Chrome • Last active now
                          </p>
                        </div>
                        <button className="btn-secondary w-full mt-3">Sign Out All Other Sessions</button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Notifications Tab */}
              {activeTab === 'notifications' && (
                <div className="space-y-6">
                  <div className="card">
                    <div className="card-header">
                      <h3 className="font-semibold flex items-center space-x-2">
                        <Bell className="w-5 h-5 text-blue-600" />
                        <span>Notification Preferences</span>
                      </h3>
                    </div>
                    <div className="card-body space-y-4">
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900">Email on Document Processing Complete</p>
                          <p className="text-sm text-gray-600">Get notified when processing finishes</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={notifications.emailOnCompletion}
                          onChange={(e) =>
                            setNotifications({
                              ...notifications,
                              emailOnCompletion: e.target.checked,
                            })
                          }
                          className="w-5 h-5 text-blue-600 rounded"
                        />
                      </div>

                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900">Email on Processing Error</p>
                          <p className="text-sm text-gray-600">Alert if document processing fails</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={notifications.emailOnError}
                          onChange={(e) =>
                            setNotifications({
                              ...notifications,
                              emailOnError: e.target.checked,
                            })
                          }
                          className="w-5 h-5 text-blue-600 rounded"
                        />
                      </div>

                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900">Daily Digest</p>
                          <p className="text-sm text-gray-600">Receive daily summary of submissions</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={notifications.dailyDigest}
                          onChange={(e) =>
                            setNotifications({
                              ...notifications,
                              dailyDigest: e.target.checked,
                            })
                          }
                          className="w-5 h-5 text-blue-600 rounded"
                        />
                      </div>

                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <p className="font-medium text-gray-900">New Features & Updates</p>
                          <p className="text-sm text-gray-600">Learn about new features and improvements</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={notifications.newFeatures}
                          onChange={(e) =>
                            setNotifications({
                              ...notifications,
                              newFeatures: e.target.checked,
                            })
                          }
                          className="w-5 h-5 text-blue-600 rounded"
                        />
                      </div>

                      <button
                        onClick={handleSaveNotifications}
                        className="btn-primary w-full flex items-center justify-center space-x-2"
                      >
                        <Save className="w-4 h-4" />
                        <span>Save Preferences</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Data Tab */}
              {activeTab === 'data' && (
                <div className="space-y-6">
                  <div className="card">
                    <div className="card-header">
                      <h3 className="font-semibold flex items-center space-x-2">
                        <HardDrive className="w-5 h-5 text-blue-600" />
                        <span>Data & Storage</span>
                      </h3>
                    </div>
                    <div className="card-body space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Data Retention Period
                        </label>
                        <select
                          value={dataRetention.retentionDays}
                          onChange={(e) =>
                            setDataRetention({
                              ...dataRetention,
                              retentionDays: parseInt(e.target.value),
                            })
                          }
                          className="input-field"
                        >
                          <option value={30}>30 days</option>
                          <option value={60}>60 days</option>
                          <option value={90}>90 days</option>
                          <option value={180}>6 months</option>
                          <option value={365}>1 year</option>
                        </select>
                        <p className="text-xs text-gray-600 mt-2">
                          Documents will be automatically deleted after this period
                        </p>
                      </div>

                      <div className="border-t pt-4">
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div>
                            <p className="font-medium text-gray-900">
                              Auto-delete Processed Documents
                            </p>
                            <p className="text-sm text-gray-600">Remove files after processing completes</p>
                          </div>
                          <input
                            type="checkbox"
                            checked={dataRetention.autoDeleteProcessed}
                            onChange={(e) =>
                              setDataRetention({
                                ...dataRetention,
                                autoDeleteProcessed: e.target.checked,
                              })
                            }
                            className="w-5 h-5 text-blue-600 rounded"
                          />
                        </div>
                      </div>

                      <div className="border-t pt-4">
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div>
                            <p className="font-medium text-gray-900">Backup Enabled</p>
                            <p className="text-sm text-gray-600">Keep encrypted backups of submissions</p>
                          </div>
                          <input
                            type="checkbox"
                            checked={dataRetention.backupEnabled}
                            onChange={(e) =>
                              setDataRetention({
                                ...dataRetention,
                                backupEnabled: e.target.checked,
                              })
                            }
                            className="w-5 h-5 text-blue-600 rounded"
                          />
                        </div>
                      </div>

                      <button
                        onClick={handleSaveDataSettings}
                        className="btn-primary w-full flex items-center justify-center space-x-2"
                      >
                        <Save className="w-4 h-4" />
                        <span>Save Data Settings</span>
                      </button>

                      <div className="border-t pt-4">
                        <p className="text-sm text-gray-600 mb-3">📊 Storage Usage: 2.3 GB / 100 GB</p>
                        <div className="w-full bg-gray-200 rounded-full h-3">
                          <div
                            className="bg-gradient-to-r from-yellow-500 to-orange-500 h-3 rounded-full"
                            style={{ width: '23%' }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* General Settings */}
              <div className="mt-8 space-y-4">
                <button
                  onClick={handleResetDefaults}
                  className="btn-secondary w-full flex items-center justify-center space-x-2"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>Reset All Settings to Defaults</span>
                </button>

                <button
                  onClick={handleLogout}
                  className="btn-danger w-full flex items-center justify-center space-x-2"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </main>
        </div>
      </div>
    </>
  );
}
