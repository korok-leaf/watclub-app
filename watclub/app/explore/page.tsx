import Header from '@/components/Header'
import Filter from '@/components/Filter'
import ClubsDisplay from '@/components/ClubsDisplay'

export default function ExplorePage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      {/* Main content */}
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters - Left Side */}
          <aside className="lg:col-span-1">
            <Filter />
          </aside>
          
          {/* Clubs Display - Right Side */}
          <section className="lg:col-span-3">
            <ClubsDisplay />
          </section>
        </div>
      </main>
    </div>
  )
}
