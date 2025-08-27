'use client'

import { useState } from 'react'
import ClubCard from './ClubCard'
import { cn } from '@/lib/utils'

const tabs = ['All', 'WUSA', 'Design', 'Faculty', 'Sports'] as const
type TabType = typeof tabs[number]

// Mock data - replace with actual API call
const mockClubs = [
  {
    id: '1',
    name: 'UW Blueprint',
    description: 'A student organization that creates technology for social good. We partner with non-profits to build custom software solutions.',
    reviewCount: 45,
    avgRating: 4.8,
    recommendPercentage: 96
  },
  {
    id: '2',
    name: 'WATonomous',
    description: 'University of Waterloo\'s autonomous vehicle student design team. Building self-driving cars and competing internationally.',
    reviewCount: 32,
    avgRating: 4.6,
    recommendPercentage: 91
  },
  // Add more mock data as needed
]

export default function ClubsDisplay() {
  const [activeTab, setActiveTab] = useState<TabType>('All')

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
      <div className="grid gap-4">
        {mockClubs.map((club) => (
          <ClubCard
            key={club.id}
            name={club.name}
            description={club.description}
            reviewCount={club.reviewCount}
            avgRating={club.avgRating}
            recommendPercentage={club.recommendPercentage}
          />
        ))}
      </div>
    </div>
  )
}
