'use client'

import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="bg-background mt-16">
        <div className="mt-8 py-4 border-t text-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} WatClub. Made with ❤️ by UW students.</p>
        </div>
    </footer>
  )
}
