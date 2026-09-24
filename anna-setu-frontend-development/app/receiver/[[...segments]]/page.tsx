import ReceiverApp from '@/components/receiver-app'

export default async function ReceiverRoute({
  params,
}: {
  params: Promise<{ segments?: string[] }>
}) {
  const { segments = [] } = await params
  return <ReceiverApp path={`/receiver/${segments.join('/')}`} />
}
