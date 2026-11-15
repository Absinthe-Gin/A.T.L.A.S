import { useState } from 'react'
import { useSearchParams } from 'react-router'

import { PageContainer, PageHeader } from '@/components/PageHeader'
import { FinanceMonth } from '@/features/finance/components/FinanceMonth'
import { MonthSwitcher } from '@/features/finance/components/MonthSwitcher'
import { toMonth } from '@/utils/money'

const MONTH = /^\d{4}-(0[1-9]|1[0-2])$/

export function FinancePage() {
  // The month lives in the URL, so it survives reloads and can be shared.
  const [params, setParams] = useSearchParams()
  const [currentMonth] = useState(() => toMonth(new Date()))
  const requested = params.get('month')
  const month = requested && MONTH.test(requested) ? requested : currentMonth

  return (
    <PageContainer>
      <PageHeader
        title="Tài chính"
        description="Thu chi, ngân sách và báo cáo trong tháng. Mọi con số được Backend tính từ giao dịch đã lưu."
        actions={<MonthSwitcher month={month} onChange={(next) => setParams({ month: next })} />}
      />
      <FinanceMonth key={month} month={month} />
    </PageContainer>
  )
}
