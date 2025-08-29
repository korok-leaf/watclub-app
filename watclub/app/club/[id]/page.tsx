"use client"

import { use } from 'react'

interface ClubDetailPageProps {
  params: Promise<{
    id: string
  }>
}

export default function ClubDetailPage({ params }: ClubDetailPageProps) {
  const { id } = use(params)

  // Mock data - replace with actual data fetching later
  const mockClub = {
    id: id,
    name: "Sample Club",
    description: "This is a detailed description of the club. It includes information about what the club does, when they meet, and what activities they organize. This would normally come from your database based on the club ID.",
    category: "Academic",
    faculty: "Engineering",
    memberCount: 45,
    founded: "2020",
    meetingTime: "Thursdays 6:00 PM",
    location: "Engineering 7 Room 6440",
    website: "https://example.com",
    email: "contact@sampleclub.com",
    socialMedia: {
      instagram: "@sampleclub",
      discord: "discord.gg/sampleclub"
    },
    images: [
      "/placeholder.svg",
      "/placeholder.svg",
      "/placeholder.svg"
    ]
  }

  const mockReviews = [
    {
      id: 1,
      author: "Student A",
      rating: 5,
      date: "2024-01-15",
      comment: "Great club! Very welcoming community and lots of interesting projects to work on."
    },
    {
      id: 2,
      author: "Student B",
      rating: 4,
      date: "2024-01-10",
      comment: "Good learning opportunities. The meetings are well organized and informative."
    },
    {
      id: 3,
      author: "Student C",
      rating: 5,
      date: "2024-01-05",
      comment: "Amazing experience! Met lots of like-minded people and learned so much."
    }
  ]

  const renderStars = (rating: number) => {
    return "★".repeat(rating) + "☆".repeat(5 - rating)
  }

  const averageRating = mockReviews.reduce((sum, review) => sum + review.rating, 0) / mockReviews.length

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
            <h1 className="text-3xl font-bold mb-2">{mockClub.name}</h1>
            <div className="flex flex-wrap gap-4 text-blue-100">
              <span className="bg-blue-700 px-3 py-1 rounded-full text-sm">{mockClub.category}</span>
              <span className="bg-blue-700 px-3 py-1 rounded-full text-sm">{mockClub.faculty}</span>
            </div>
          </div>
          
          {/* Club Images */}
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {mockClub.images.map((image, index) => (
                <div key={index} className="aspect-video bg-gray-200 rounded-lg overflow-hidden">
                  <img 
                    src={image} 
                    alt={`${mockClub.name} image ${index + 1}`}
                    className="w-full h-full object-cover"
                  />
                </div>
              ))}
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
              <p className="text-gray-700 leading-relaxed">{mockClub.description}</p>
            </div>

            {/* Reviews Section */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold">Reviews</h2>
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{renderStars(Math.round(averageRating))}</span>
                  <span className="text-gray-600">({mockReviews.length} reviews)</span>
                </div>
              </div>

              {/* Individual Reviews */}
              <div className="space-y-4">
                {mockReviews.map((review) => (
                  <div key={review.id} className="border-b border-gray-200 pb-4 last:border-b-0">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                          {review.author.charAt(0)}
                        </div>
                        <span className="font-medium">{review.author}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-yellow-500">{renderStars(review.rating)}</span>
                        <span className="text-gray-500 text-sm">{review.date}</span>
                      </div>
                    </div>
                    <p className="text-gray-700 ml-11">{review.comment}</p>
                  </div>
                ))}
              </div>

              {/* Add Review Button */}
              <div className="mt-6 pt-4 border-t border-gray-200">
                <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition duration-200">
                  Write a Review
                </button>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            {/* Club Info */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h3 className="text-xl font-bold mb-4">Club Information</h3>
              <div className="space-y-3">
                <div>
                  <span className="font-medium text-gray-700">Members:</span>
                  <span className="ml-2">{mockClub.memberCount}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Founded:</span>
                  <span className="ml-2">{mockClub.founded}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Meeting Time:</span>
                  <span className="ml-2">{mockClub.meetingTime}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Location:</span>
                  <span className="ml-2">{mockClub.location}</span>
                </div>
              </div>
            </div>

            {/* Contact Info */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h3 className="text-xl font-bold mb-4">Contact</h3>
              <div className="space-y-3">
                <div>
                  <span className="font-medium text-gray-700">Website:</span>
                  <a href={mockClub.website} className="ml-2 text-blue-600 hover:underline block">
                    {mockClub.website}
                  </a>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Email:</span>
                  <a href={`mailto:${mockClub.email}`} className="ml-2 text-blue-600 hover:underline block">
                    {mockClub.email}
                  </a>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Instagram:</span>
                  <span className="ml-2">{mockClub.socialMedia.instagram}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Discord:</span>
                  <span className="ml-2">{mockClub.socialMedia.discord}</span>
                </div>
              </div>
            </div>

            {/* Join Club Button */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <button className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 transition duration-200 font-medium">
                Join This Club
              </button>
              <p className="text-gray-600 text-sm mt-2 text-center">
                Connect with {mockClub.memberCount} other members
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