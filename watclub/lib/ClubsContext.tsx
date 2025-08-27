'use client'

import { createContext, useContext, useState, useEffect, useMemo } from 'react'
import MiniSearch from 'minisearch'

interface Club {
  id: string
  name: string
  description: string
  orgType: string
  reviewCount: number
  avgRating: number
  recommendPercentage: number
}

interface ClubsContextType {
  clubs: Club[]
  loading: boolean
  error: string | null
  searchQuery: string
  setSearchQuery: (query: string) => void
  searchResults: Club[]
  getTopSearchResults: (query: string, limit?: number) => Club[]
}

const ClubsContext = createContext<ClubsContextType | undefined>(undefined)

export function ClubsProvider({ children }: { children: React.ReactNode }) {
  const [clubs, setClubs] = useState<Club[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

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

  // Initialize MiniSearch
  const searchIndex = useMemo(() => {
    if (clubs.length === 0) return null
    
    const miniSearch = new MiniSearch<Club>({
      fields: ['name', 'description'], // Fields to search
      storeFields: ['id', 'name', 'description', 'orgType', 'reviewCount', 'avgRating', 'recommendPercentage'], // Fields to store
      searchOptions: {
        boost: { name: 2 }, // Prioritize name matches
        fuzzy: 0.2, // Typo tolerance: allow up to 20% of the term length as typos
        prefix: true, // Enable prefix search for autocomplete
      }
    })
    
    // Add all clubs to the index
    miniSearch.addAll(clubs)
    
    return miniSearch
  }, [clubs])

  // Get all search results
  const searchResults = useMemo(() => {
    if (!searchQuery.trim() || !searchIndex) return clubs
    
    const results = searchIndex.search(searchQuery, {
      fuzzy: 0.2,
      prefix: true,
      boost: { name: 2 }
    })
    
    // Map the search results back to club objects
    return results.map(result => clubs.find(club => club.id === result.id)!).filter(Boolean)
  }, [searchIndex, clubs, searchQuery])

  // Get top N results for dropdown
  const getTopSearchResults = (query: string, limit = 5) => {
    if (!query.trim() || !searchIndex) return []
    
    const results = searchIndex.search(query, {
      fuzzy: 0.2,
      prefix: true,
      boost: { name: 2 }
    })
    
    // Return top N results
    return results
      .slice(0, limit)
      .map(result => clubs.find(club => club.id === result.id)!)
      .filter(Boolean)
  }

  const value = {
    clubs,
    loading,
    error,
    searchQuery,
    setSearchQuery,
    searchResults,
    getTopSearchResults
  }

  return <ClubsContext.Provider value={value}>{children}</ClubsContext.Provider>
}

export function useClubsContext() {
  const context = useContext(ClubsContext)
  if (context === undefined) {
    throw new Error('useClubsContext must be used within a ClubsProvider')
  }
  return context
}
