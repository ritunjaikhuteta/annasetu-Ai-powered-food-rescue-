import DriverApp from '@/components/driver-app'

export default async function DriverRoute({
  params,
}: {
  params: Promise<{ segments?: string[] }>
}) {
  const { segments = [] } = await params
  return <DriverApp path={`/driver/${segments.join('/')}`} />
}
