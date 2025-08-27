'use client'

import { useState, useEffect } from 'react'

interface Club {
  id: string
  name: string
  description: string
  orgType: string
  reviewCount: number
  avgRating: number
  recommendPercentage: number
}

interface UseClubsReturn {
  clubs: Club[]
  loading: boolean
  error: string | null
}

export function useClubs(): UseClubsReturn {
  const [clubs, setClubs] = useState<Club[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchClubs = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/clubs')
        
        if (!response.ok) {
          throw new Error('Failed to fetch clubs')
        }
        
        const data = await response.json()
        console.log('club data', data)
        setClubs(data.clubs)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchClubs()
  }, [])

  return { clubs, loading, error }
}
