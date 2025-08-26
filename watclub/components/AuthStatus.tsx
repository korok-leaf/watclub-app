'use client'

import { useEffect, useState } from 'react'
import { supabase, signOut } from '@/lib/supabaseClient'
import type { User } from '@supabase/supabase-js'

export default function AuthStatus() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Get initial session
    const getInitialSession = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      setUser(session?.user ?? null)
      setLoading(false)
    }

    getInitialSession()

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setUser(session?.user ?? null)
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [])

  const handleSignOut = async () => {
    await signOut()
  }

  if (loading) {
    return <div className="p-4 text-center">Loading...</div>
  }

  return (
    <div className="fixed top-4 right-4 bg-white p-4 rounded-lg shadow-md border">
      {user ? (
        <div className="text-sm">
          <p className="text-green-600 font-medium">✓ Signed in as:</p>
          <p className="text-gray-700">{user.email}</p>
          <button
            onClick={handleSignOut}
            className="mt-2 px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
          >
            Sign Out
          </button>
        </div>
      ) : (
        <div className="text-sm">
          <p className="text-gray-600 mb-2">Not signed in</p>
          <div className="space-x-2">
            <a
              href="/login"
              className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
            >
              Login
            </a>
            <a
              href="/signup"
              className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
            >
              Sign Up
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
