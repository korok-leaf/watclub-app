'use client'

import Link from 'next/link'
import { useAuth } from '@/lib/AuthContext'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { ThemeToggle } from '@/components/theme-toggle'
import { SearchBar } from '@/components/SearchBar'

export default function Header() {
  const { user, loading } = useAuth()

  return (
    <header className="border-b bg-background">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="flex h-16 items-center justify-between gap-4">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-[#FFD700] via-[#FFA500] to-[#FF6B35] bg-clip-text text-transparent">
              WatClub
            </h1>
          </Link>

          {/* Search Bar */}
          <SearchBar containerClassName="flex-1 max-w-xl" />

          {/* Auth Section */}
          <div className="flex items-center space-x-2">
            <ThemeToggle />
            
            {loading ? (
              <div className="h-10 w-10 animate-pulse rounded-full bg-muted" />
            ) : user ? (
              <Avatar>
                <AvatarImage src="/placeholder-logo.png" alt="User" />
                <AvatarFallback>
                  {user.email?.charAt(0).toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
            ) : (
              <>
                <Button variant="ghost" asChild>
                  <Link href="/login">Log in</Link>
                </Button>
                <Button asChild>
                  <Link href="/signup">Sign up</Link>
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
