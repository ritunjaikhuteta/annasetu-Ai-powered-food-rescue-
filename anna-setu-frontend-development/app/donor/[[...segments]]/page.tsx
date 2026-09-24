import DonorApp from '@/components/donor-app'

export default async function DonorRoute({ params }: { params: Promise<{ segments?: string[] }> }) {
  const { segments = [] } = await params
  return <DonorApp path={`/donor/${segments.join('/')}`} />
}
