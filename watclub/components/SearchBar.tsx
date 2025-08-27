'use client'

import { useState, useRef, useEffect } from 'react'
import { Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useClubsContext } from '@/lib/ClubsContext'
import { useRouter } from 'next/navigation'

interface SearchBarProps extends React.InputHTMLAttributes<HTMLInputElement> {
  containerClassName?: string
}

export function SearchBar({ className, containerClassName, ...props }: SearchBarProps) {
  const [localQuery, setLocalQuery] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()
  
  const { setSearchQuery, getTopSearchResults } = useClubsContext()
  const topResults = getTopSearchResults(localQuery)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setLocalQuery(value)
    setShowDropdown(value.length > 0)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSearchQuery(localQuery)
    setShowDropdown(false)
    inputRef.current?.blur()
  }

  const handleClubClick = (clubId: string) => {
    setShowDropdown(false)
    router.push(`/club/${clubId}`)
  }

  return (
    <div className={cn("relative", containerClassName)} ref={dropdownRef}>
      <form onSubmit={handleSubmit}>
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          ref={inputRef}
          type="search"
          value={localQuery}
          onChange={handleInputChange}
          className={cn(
            "flex h-10 w-full rounded-md bg-background pl-10 pr-4 py-2 text-base",
            "placeholder:text-muted-foreground",
            "focus:outline-none",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "md:text-sm",
            "border border-gray-300 dark:border-gray-700",
            className
          )}
          placeholder="Search clubs..."
          {...props}
        />
      </form>

      {/* Dropdown */}
      {showDropdown && topResults.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-background border rounded-md shadow-lg z-50 overflow-hidden">
          {topResults.map((club) => (
            <button
              key={club.id}
              onClick={() => handleClubClick(club.id)}
              className="w-full px-4 py-3 text-left hover:bg-accent transition-colors border-b last:border-0"
            >
              <div className="font-medium text-sm">{club.name}</div>
              <div className="text-xs text-muted-foreground line-clamp-1">
                {club.description}
              </div>
            </button>
          ))}
          <button
            onClick={handleSubmit}
            className="w-full px-4 py-2 text-center text-sm text-muted-foreground hover:bg-accent transition-colors"
          >
            Press Enter to see all results
          </button>
        </div>
      )}
    </div>
  )
}
