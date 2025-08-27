'use client'

import Link from 'next/link'
import { useAuth } from '@/lib/AuthContext'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { ThemeToggle } from '@/components/theme-toggle'
import { SearchBar } from '@/components/SearchBar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { User, LogOut } from 'lucide-react'

export default function Header() {
  const { user, loading, signOut } = useAuth()

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b bg-background">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="flex h-16 items-center justify-between gap-4">
          {/* Logo */}
          <Link href={user ? "/explore" : "/"} className="flex items-center space-x-2">
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
              <DropdownMenu modal={false}>
                <DropdownMenuTrigger asChild>
                  <Avatar className="cursor-pointer">
                    <AvatarImage src="/placeholder-logo.png" alt="User" />
                    <AvatarFallback>
                      {user.email?.charAt(0).toUpperCase() || 'U'}
                    </AvatarFallback>
                  </Avatar>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-36">
                  <DropdownMenuItem asChild>
                    <Link href="/profile" className="flex items-center">
                      <User className="mr-2 h-4 w-4" />
                      Profile
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={signOut} className="flex items-center cursor-pointer">
                    <LogOut className="mr-2 h-4 w-4" />
                    Log out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
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
