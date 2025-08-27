export const TAGS = [
  // Academic
  "Academic",
  "Science", 
  "Math",
  
  // Tech
  "Software",
  "AI",
  "Robotics",
  "Hardware",
  
  // Business
  "Business",
  "Finance",
  "Consulting",
  "Entrepreneurship",
  
  // Environment & Health
  "Sustainability",
  "Wellness",
  "Mental Health",
  
  // Sports & Recreation
  "Sports",
  "Recreation",
  "Outdoors",
  
  // Arts & Media
  "Arts",
  "Music",
  "Dance",
  "Theatre",
  "Media",
  
  // Gaming
  "Gaming",
  "Esports",
  "Boardgames",
  
  // Community & Culture
  "Volunteer",
  "Advocacy",
  "Cultural",
  "LGBTQ",
  "Leadership",
] as const

export type Tag = typeof TAGS[number]

// Group tags by category for better UI
export const TAG_CATEGORIES = {
  "Academic": ["Academic", "Science", "Math"],
  "Technology": ["Software", "AI", "Robotics", "Hardware"],
  "Business": ["Business", "Finance", "Consulting", "Entrepreneurship"],
  "Health & Environment": ["Sustainability", "Wellness", "Mental Health"],
  "Sports & Recreation": ["Sports", "Recreation", "Outdoors"],
  "Arts & Media": ["Arts", "Music", "Dance", "Theatre", "Media"],
  "Gaming": ["Gaming", "Esports", "Boardgames"],
  "Community": ["Volunteer", "Advocacy", "Cultural", "LGBTQ", "Leadership"],
} as const
