'use client'

import Link from 'next/link'
import { signOut } from '@/lib/supabaseClient'
import { useAuth } from '@/hooks/useAuth'

export default function ProfilePage() {
  const { user, loading } = useAuth()

  const handleSignOut = async () => {
    await signOut()
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  // Not logged in - show login/signup prompt
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6 text-center">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Profile</h1>
            <p className="text-gray-600">You need to be logged in to view your profile</p>
          </div>
          
          <div className="space-y-3">
            <Link
              href="/login"
              className="block w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition duration-200"
            >
              Sign In
            </Link>
            
            <Link
              href="/signup"
              className="block w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition duration-200"
            >
              Create Account
            </Link>
            
            <Link
              href="/"
              className="block w-full text-gray-600 hover:text-gray-800 transition duration-200"
            >
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // Logged in - show profile info
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Header */}
          <div className="bg-blue-600 px-6 py-4">
            <h1 className="text-2xl font-bold text-white">Your Profile</h1>
          </div>
          
          {/* Profile Content */}
          <div className="p-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                  {user.email}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  User ID
                </label>
                <p className="text-gray-600 bg-gray-50 px-3 py-2 rounded-md text-sm font-mono">
                  {user.id}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Display Name
                </label>
                <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded-md">
                  {user.user_metadata?.display_name || user.user_metadata?.full_name || 'Not set'}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Account Created
                </label>
                <p className="text-gray-600 bg-gray-50 px-3 py-2 rounded-md">
                  {new Date(user.created_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Confirmed
                </label>
                <p className={`px-3 py-2 rounded-md ${
                  user.email_confirmed_at 
                    ? 'text-green-700 bg-green-50' 
                    : 'text-red-700 bg-red-50'
                }`}>
                  {user.email_confirmed_at ? '✓ Confirmed' : '✗ Not confirmed'}
                </p>
              </div>
            </div>
            
            {/* Actions */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={handleSignOut}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition duration-200"
                >
                  Sign Out
                </button>
                
                <Link
                  href="/"
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition duration-200 text-center"
                >
                  Back to Home
                </Link>
              </div>
            </div>
          </div>
        </div>
        
        {/* Debug Info (remove in production) */}
        <div className="mt-6 bg-gray-800 text-white p-4 rounded-lg">
          <h3 className="font-bold mb-2">Debug Info:</h3>
          <pre className="text-xs overflow-x-auto">
            {JSON.stringify(user, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  )
}
