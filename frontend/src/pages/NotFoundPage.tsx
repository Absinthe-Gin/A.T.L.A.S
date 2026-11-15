import { Link } from 'react-router'

import { IconAlert } from '@/components/icons'
import { PageContainer } from '@/components/PageHeader'
import { buttonClasses } from '@/components/ui/buttonClasses'
import { Card } from '@/components/ui/Card'
import { EmptyState } from '@/components/ui/EmptyState'

export function NotFoundPage() {
  return (
    <PageContainer>
      <Card>
        <EmptyState
          icon={<IconAlert />}
          title="Không tìm thấy trang"
          description="Đường dẫn bạn truy cập không tồn tại hoặc đã được thay đổi."
          action={
            <Link to="/" className={buttonClasses('primary', 'md')}>
              Về trang chủ
            </Link>
          }
        />
      </Card>
    </PageContainer>
  )
}
