import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY! 
)

export async function POST(request: NextRequest) {
  try {
    const { id } = await request.json()

    if (!id) {
      return NextResponse.json(
        { error: 'Club ID is required' },
        { status: 400 }
      )
    }

    const { data: club, error } = await supabase
      .from('clubs')
      .select('id, name, description, org_type, tags, total_reviews, total_recommends, avg_review')
      .eq('id', id)
      .single()

    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json(
        { error: 'Failed to fetch club' },
        { status: 500 }
      )
    }

    if (!club) {
      return NextResponse.json(
        { error: 'Club not found' },
        { status: 404 }
      )
    }

    // Transform data for frontend
    const transformedClub = {
      id: club.id,
      name: club.name,
      description: club.description,
      orgType: club.org_type,
      tags: club.tags,
      reviewCount: club.total_reviews || 0,
      avgRating: club.avg_review || 0,
      recommendPercentage: club.total_reviews > 0 
        ? Math.round((club.total_recommends / club.total_reviews) * 100)
        : 0
    }

    return NextResponse.json({ club: transformedClub })
  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}