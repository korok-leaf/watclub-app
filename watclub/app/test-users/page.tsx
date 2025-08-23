import UserForm from '@/components/UserForm'

export default function TestUsersPage() {
  return (
    <div className="min-h-screen bg-background py-12">
      <div className="container mx-auto px-4">
        <h1 className="text-3xl font-bold text-center mb-8">
          Test User Management
        </h1>
        <UserForm />
      </div>
    </div>
  )
}
