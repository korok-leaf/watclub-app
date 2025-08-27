'use client'

interface ClubCardProps {
  name: string
  description: string
  reviewCount: number
  avgRating: number
  recommendPercentage: number
}

export default function ClubCard({
  name,
  description,
  reviewCount,
  avgRating,
  recommendPercentage
}: ClubCardProps) {
  return (
    <div className="rounded-lg border bg-card p-6 hover:shadow-lg transition-all cursor-pointer">
      <h3 className="text-lg font-semibold mb-2">{name}</h3>
      
      {/* Truncated description */}
      <p className="text-muted-foreground text-sm mb-4 line-clamp-2">
        {description.slice(0, 150) + '...'}
      </p>
      
      {/* Stats */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-3 text-muted-foreground">
          <span>{reviewCount} reviews</span>
          <span className="flex items-center gap-1">
            <span className="text-yellow-500">★</span>
            {avgRating.toFixed(1)}
          </span>
        </div>
        <span className="text-green-600 font-medium">
          {recommendPercentage}% recommend
        </span>
      </div>
    </div>
  )
}
