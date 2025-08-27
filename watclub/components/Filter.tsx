'use client'

import { useState } from 'react'
import { useClubsContext } from '@/lib/ClubsContext'
import { TAG_CATEGORIES } from '@/lib/tags'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronUp } from 'lucide-react'

export default function Filter() {
  const { selectedTags, setSelectedTags } = useClubsContext()
  const [expandedCategories, setExpandedCategories] = useState<string[]>([])

  const toggleTag = (tag: string) => {
    setSelectedTags(
      selectedTags.includes(tag)
        ? selectedTags.filter(t => t !== tag)
        : [...selectedTags, tag]
    )
  }

  const toggleCategory = (category: string) => {
    setExpandedCategories(
      expandedCategories.includes(category)
        ? expandedCategories.filter(c => c !== category)
        : [...expandedCategories, category]
    )
  }

  const clearFilters = () => {
    setSelectedTags([])
  }

  return (
    <div className="sticky top-24">
      <div className="rounded-lg border bg-card p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Filters</h2>
          {selectedTags.length > 0 && (
            <Button 
              className="h-auto py-1 px-2 text-xs" 
              variant="ghost" 
              size="sm" 
              onClick={clearFilters}
            >
              Clear all
            </Button>
          )}
        </div>
        
        <div className="space-y-3">
          {Object.entries(TAG_CATEGORIES).map(([category, tags]) => (
            <div key={category} className="border-b pb-3 last:border-0">
              <button
                onClick={() => toggleCategory(category)}
                className="flex items-center justify-between w-full text-left hover:text-primary transition-colors"
              >
                <span className="font-medium text-sm">{category}</span>
                {expandedCategories.includes(category) ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </button>
              
              {expandedCategories.includes(category) && (
                <div className="mt-2 space-y-2">
                  {tags.map(tag => (
                    <div key={tag} className="flex items-center space-x-2">
                      <Checkbox
                        id={tag}
                        checked={selectedTags.includes(tag)}
                        onCheckedChange={() => toggleTag(tag)}
                      />
                      <Label
                        htmlFor={tag}
                        className="text-sm cursor-pointer flex-1"
                      >
                        {tag}
                      </Label>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
