import { useParams } from 'react-router'

import { PageContainer } from '@/components/PageHeader'
import { PlanView } from '@/features/travel/components/PlanView'

export function TravelPlanPage() {
  const { planId = '' } = useParams()
  return (
    <PageContainer>
      {/* Keyed so moving between plans starts from a clean state. */}
      <PlanView key={planId} planId={planId} />
    </PageContainer>
  )
}
