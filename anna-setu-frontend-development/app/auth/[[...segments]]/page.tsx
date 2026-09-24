import AuthApp from '@/components/auth-app'

export default async function AuthPage({ params }: { params: Promise<{ segments?: string[] }> }) {
  const { segments = [] } = await params
  return <AuthApp pathname={`/auth/${segments.join('/')}`} />
}
