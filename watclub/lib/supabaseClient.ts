import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL as string
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Types for your users table
export interface User {
  id?: number // bigint, auto-generated
  created_at?: string // timestamp, auto-generated
  first_name: string
  last_name: string
  faculty: string | null // nullable in your schema
}

export interface UserInsert {
  first_name: string
  last_name: string
  faculty?: string | null // optional since it's nullable
}

// Function to insert a new user
export const insertUser = async (userData: UserInsert) => {
  console.log('Attempting to insert user:', userData)
  
  const { data, error } = await supabase
    .from('users')
    .insert(userData)
    .select() // Return the inserted data
  
  if (error) {
    console.error('Error inserting user:', error)
    console.error('Error details:', {
      message: error.message,
      details: error.details,
      hint: error.hint,
      code: error.code
    })
    return { data: null, error }
  }
  
  console.log('User inserted successfully:', data)
  return { data, error: null }
}

// Function to insert multiple users
export const insertMultipleUsers = async (usersData: UserInsert[]) => {
  const { data, error } = await supabase
    .from('users')
    .insert(usersData)
    .select()
  
  if (error) {
    console.error('Error inserting users:', error)
    return { data: null, error }
  }
  
  console.log('Users inserted successfully:', data)
  return { data, error: null }
}

// Function to get all users (for testing)
export const getAllUsers = async () => {
  const { data, error } = await supabase
    .from('users')
    .select('*')
    .order('created_at', { ascending: false })
  
  if (error) {
    console.error('Error fetching users:', error)
    return { data: null, error }
  }
  
  return { data, error: null }
}
