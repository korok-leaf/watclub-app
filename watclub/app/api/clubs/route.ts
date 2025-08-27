import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY! 
)

export async function GET() {
  try {

    const { data: clubs, error } = await supabase
      .from('clubs')
      .select('id, name, description, org_type, total_reviews, total_recommends, avg_review')
      .order('name')

    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json(
        { error: 'Failed to fetch clubs' },
        { status: 500 }
      )
    }

    // Transform data for frontend
    const transformedClubs = clubs?.map(club => ({
      id: club.id,
      name: club.name,
      description: club.description,
      orgType: club.org_type,
      reviewCount: club.total_reviews || 0,
      avgRating: club.avg_review || 0,
      recommendPercentage: club.total_reviews > 0 
        ? Math.round((club.total_recommends / club.total_reviews) * 100)
        : 0
    })) || []

    return NextResponse.json({ clubs: transformedClubs })
  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
