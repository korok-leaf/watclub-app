'use client'

import { Search } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SearchBarProps extends React.InputHTMLAttributes<HTMLInputElement> {
  containerClassName?: string
}

export function SearchBar({ className, containerClassName, ...props }: SearchBarProps) {
  return (
    <div className={cn("relative", containerClassName)}>
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <input
        type="search"
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
    </div>
  )
}
