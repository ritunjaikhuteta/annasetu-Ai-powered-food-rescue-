import AdminApp from '@/components/admin-app'

export default async function AdminRoute({
  params,
}: {
  params: Promise<{ segments?: string[] }>
}) {
  const { segments = [] } = await params
  return <AdminApp path={`/admin/${segments.join('/')}`} />
}
