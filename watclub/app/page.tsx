import ArcGalleryHero from "@/components/arc-gallery-hero"

export default function Home() {
  const images = [
    "/design/uw-blueprint.png",
    "/design/waterloop.png", 
    "/design/watai.jpeg",
    "/design/uw-formula-electric.png",
    "/design/robotics-team-uwrt.png",
    "/design/uw-reality-labs.png",
    "/wusa/tech-uw.jpg",
    "/wusa/ascend-canada-waterloo-chapter.jpg",
    "/faculty/engsoc/uwaterloo-engiqueers.png",
    "/faculty/engsoc/women-in-engineering.png",
    "/design/electrium-mobility.png",
  ]

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