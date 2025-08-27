'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/AuthContext'
import ArcGalleryHero from "@/components/arc-gallery-hero"

export default function Home() {
  const { user, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && user) {
      router.push('/explore')
    }
  }, [user, loading, router])

  const images = [
    "/design/watai.jpeg",
    "/design/watonomous.jpeg", 
    "/wusa/chinese-students-association-csa-uw.jpg",
    "/wusa/uw-poker-studies-club.jpg",
    "/design/uw-blueprint.png",
    "/faculty/mathsoc/computer-science-club.png",
    "/faculty/engsoc/women-in-engineering.avif",
    "/design/wat-street.jpeg",
    "/sports/uwdbc.avif",
    "/sports/badminton.png",
    "/wusa/human-vs-zombies.jpg"
  ]

  // Show loading state while checking auth
  if (loading) {
    return (
      <main className="relative min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </main>
    )
  }

  // Only show hero if not logged in
  return (
    <main className="relative min-h-screen bg-background">
      <ArcGalleryHero
        images={images}
        startAngle={20}
        endAngle={160}
        radiusLg={480}
        radiusMd={360}
        radiusSm={260}
        cardSizeLg={120}
        cardSizeMd={100}
        cardSizeSm={80}
        className="pt-16 pb-16 md:pt-20 md:pb-20 lg:pt-24 lg:pb-24"
      />
    </main>
  )
}