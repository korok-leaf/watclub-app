'use client'

import { useState } from 'react'
import { insertUser, getAllUsers, type UserInsert } from '@/lib/supabaseClient'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function UserForm() {
  const [formData, setFormData] = useState<UserInsert>({
    first_name: '',
    last_name: '',
    faculty: ''
  })
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState('')

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setMessage('')

    try {
      const { data, error } = await insertUser(formData)
      
      if (error) {
        setMessage(`Error: ${error.message}`)
      } else {
        setMessage('User added successfully!')
        // Reset form
        setFormData({
          first_name: '',
          last_name: '',
          faculty: ''
        })
      }
    } catch (err) {
      setMessage('An unexpected error occurred')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleTestFetch = async () => {
    setIsLoading(true)
    try {
      const { data, error } = await getAllUsers()
      if (error) {
        setMessage(`Error fetching users: ${error.message}`)
      } else {
        setMessage(`Found ${data?.length || 0} users. Check console for details.`)
        console.log('All users:', data)
      }
    } catch (err) {
      setMessage('Error fetching users')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Add New User</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="first_name">First Name</Label>
            <Input
              id="first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleInputChange}
              required
              placeholder="Enter first name"
            />
          </div>
          
          <div>
            <Label htmlFor="last_name">Last Name</Label>
            <Input
              id="last_name"
              name="last_name"
              value={formData.last_name}
              onChange={handleInputChange}
              required
              placeholder="Enter last name"
            />
          </div>
          
          <div>
            <Label htmlFor="faculty">Faculty</Label>
            <Input
              id="faculty"
              name="faculty"
              value={formData.faculty || ''}
              onChange={handleInputChange}
              placeholder="e.g., Engineering, Arts, Math (optional)"
            />
          </div>
          
          <div className="flex gap-2">
            <Button 
              type="submit" 
              disabled={isLoading}
              className="flex-1"
            >
              {isLoading ? 'Adding...' : 'Add User'}
            </Button>
            
            <Button 
              type="button" 
              variant="outline"
              onClick={handleTestFetch}
              disabled={isLoading}
            >
              Test Fetch
            </Button>
          </div>
        </form>
        
        {message && (
          <div className={`mt-4 p-3 rounded ${
            message.includes('Error') 
              ? 'bg-red-100 text-red-700 border border-red-300' 
              : 'bg-green-100 text-green-700 border border-green-300'
          }`}>
            {message}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
