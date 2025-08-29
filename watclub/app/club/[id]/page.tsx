"use client"

import { use, useEffect, useState } from 'react'

interface ClubData {
  id: number
  name: string
  description: string
  orgType: string
  tags: string[]
  reviewCount: number
  avgRating: number
  recommendPercentage: number
}

interface ClubDetailPageProps {
  params: Promise<{
    id: string
  }>
}

export default function ClubDetailPage({ params }: ClubDetailPageProps) {
  const { id } = use(params)
  const [club, setClub] = useState<ClubData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchClub = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/club', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ id }),
        })

        if (!response.ok) {
          throw new Error('Failed to fetch club data')
        }

        const data = await response.json()
        setClub(data.club)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchClub()
  }, [id])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-lg shadow-md p-8">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-300 rounded mb-4"></div>
              <div className="h-4 bg-gray-300 rounded mb-2"></div>
              <div className="h-4 bg-gray-300 rounded mb-2"></div>
              <div className="h-4 bg-gray-300 rounded w-2/3"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-lg shadow-md p-8">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-gray-900 mb-4">Error</h1>
              <p className="text-gray-600">{error}</p>
              <button 
                onClick={() => window.history.back()}
                className="mt-4 text-blue-600 hover:text-blue-800"
              >
                ← Back to Clubs
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!club) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-lg shadow-md p-8">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-gray-900 mb-4">Club Not Found</h1>
              <p className="text-gray-600">The club you're looking for doesn't exist.</p>
              <button 
                onClick={() => window.history.back()}
                className="mt-4 text-blue-600 hover:text-blue-800"
              >
                ← Back to Clubs
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderStars = (rating: number) => {
    return "★".repeat(Math.round(rating)) + "☆".repeat(5 - Math.round(rating))
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Back Button */}
        <div className="mb-6">
          <button 
            onClick={() => window.history.back()}
            className="text-blue-600 hover:text-blue-800 flex items-center gap-2"
          >
            ← Back to Clubs
          </button>
        </div>

        {/* Club Header */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden mb-8">
          <div className="bg-blue-600 px-6 py-8 text-white">
            <h1 className="text-3xl font-bold mb-2">{club.name}</h1>
            <div className="flex flex-wrap gap-4 text-blue-100">
              <span className="bg-blue-700 px-3 py-1 rounded-full text-sm capitalize">{club.orgType}</span>
              {club.tags.map((tag, index) => (
                <span key={index} className="bg-blue-700 px-3 py-1 rounded-full text-sm">{tag}</span>
              ))}
            </div>
          </div>
          
          {/* Placeholder for club images - replace with actual images when available */}
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="aspect-video bg-gray-200 rounded-lg overflow-hidden flex items-center justify-center">
                <span className="text-gray-500">No images available</span>
              </div>
            </div>
          </div>
        </div>

        {/* Club Details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Description */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-2xl font-bold mb-4">About This Club</h2>
              <p className="text-gray-700 leading-relaxed">{club.description}</p>
            </div>

            {/* Reviews Section */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold">Reviews</h2>
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{renderStars(club.avgRating)}</span>
                  <span className="text-gray-600">({club.reviewCount} reviews)</span>
                </div>
              </div>

              {club.reviewCount > 0 ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-600">{club.avgRating.toFixed(1)}</div>
                      <div className="text-sm text-gray-600">Average Rating</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-600">{club.recommendPercentage}%</div>
                      <div className="text-sm text-gray-600">Would Recommend</div>
                    </div>
                  </div>
                  {/* Add individual reviews here when available */}
                  <p className="text-gray-500 italic">Individual reviews will be displayed here when available.</p>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500 mb-4">No reviews yet. Be the first to review this club!</p>
                  <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700">
                    Write a Review
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            {/* Club Info */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h3 className="text-xl font-bold mb-4">Club Information</h3>
              <div className="space-y-3">
                <div>
                  <span className="font-medium text-gray-700">Organization Type:</span>
                  <span className="ml-2 capitalize">{club.orgType}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Tags:</span>
                  <div className="ml-2 flex flex-wrap gap-1 mt-1">
                    {club.tags.map((tag, index) => (
                      <span key={index} className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Reviews:</span>
                  <span className="ml-2">{club.reviewCount}</span>
                </div>
              </div>
            </div>

            {/* Contact Info - Placeholder */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h3 className="text-xl font-bold mb-4">Contact</h3>
              <div className="space-y-3">
                <p className="text-gray-500 italic">Contact information will be available soon.</p>
              </div>
            </div>

            {/* Join Club Button */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <button className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 transition duration-200 font-medium">
                Join This Club
              </button>
              <p className="text-gray-600 text-sm mt-2 text-center">
                Connect with other members
              </p>
            </div>
          </div>
        </div>

        {/* Debug Info */}
        <div className="bg-gray-800 text-white p-4 rounded-lg">
          <h3 className="font-bold mb-2">Debug Info:</h3>
          <p className="text-sm">Club ID: {id}</p>
          <p className="text-sm">URL: /club/{id}</p>
        </div>
      </div>
    </div>
  )
}