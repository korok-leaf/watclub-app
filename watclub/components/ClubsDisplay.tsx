'use client'

import { useState, useMemo } from 'react'
import ClubCard from './ClubCard'
import { cn } from '@/lib/utils'
import { useClubsContext } from '@/lib/ClubsContext'

const tabs = ['All', 'WUSA', 'Design', 'Faculty', 'Sports'] as const
type TabType = typeof tabs[number]

export default function ClubsDisplay() {
  const [activeTab, setActiveTab] = useState<TabType>('All')
  const { searchResults, loading, error } = useClubsContext() 

  // Filter clubs based on active tab
  const filteredClubs = useMemo(() => {
    if (activeTab === 'All') return searchResults
    
    // Map tab names to org_type values
    const tabToOrgType: Record<string, string> = {
      'WUSA': 'wusa',
      'Design': 'design',
      'Faculty': 'faculty',
      'Sports': 'sports'
    }
    
    return searchResults.filter(club => club.orgType === tabToOrgType[activeTab]) // Filter searchResults
  }, [searchResults, activeTab])

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-destructive">Error loading clubs: {error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex gap-2 border-b">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "px-4 py-2 text-sm font-medium transition-colors relative",
              "hover:text-foreground",
              activeTab === tab
                ? "text-foreground"
                : "text-muted-foreground",
            )}
          >
            {tab}
            {activeTab === tab && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
            )}
          </button>
        ))}
      </div>

      {/* Clubs Grid */}
      {loading ? (
        <div className="grid gap-4">
          {/* Loading skeletons */}
          {[...Array(6)].map((_, i) => (
            <div key={i} className="rounded-lg border bg-card p-6 animate-pulse">
              <div className="h-6 bg-muted rounded w-3/4 mb-2" />
              <div className="h-4 bg-muted rounded w-full mb-1" />
              <div className="h-4 bg-muted rounded w-5/6 mb-4" />
              <div className="flex justify-between">
                <div className="h-4 bg-muted rounded w-24" />
                <div className="h-4 bg-muted rounded w-20" />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredClubs.length > 0 ? (
            filteredClubs.map((club) => (
              <ClubCard
                key={club.id}
                id={club.id}
                name={club.name}
                description={club.description}
                reviewCount={club.reviewCount}
                avgRating={club.avgRating}
                recommendPercentage={club.recommendPercentage}
              />
            ))
          ) : (
            <p className="text-muted-foreground text-center py-8">
              No clubs found in this category.
            </p>
          )}
        </div>
      )}
    </div>
  )
}