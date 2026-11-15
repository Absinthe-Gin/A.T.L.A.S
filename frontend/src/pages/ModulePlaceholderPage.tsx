import { Link } from 'react-router'

import { PageContainer, PageHeader } from '@/components/PageHeader'
import { buttonClasses } from '@/components/ui/buttonClasses'
import { NOTE_INK, NOTE_PAPER } from '@/components/ui/noteColors'
import { StickyNote } from '@/components/ui/StickyNote'
import { getModule, type ModuleId } from '@/features/modules/catalog'
import { cn } from '@/utils/cn'

/**
 * Page for a module that is designed but not implemented. It states that
 * plainly and lists what is planned; it never shows sample data as if it were real.
 */
export function ModulePlaceholderPage({ moduleId }: { moduleId: ModuleId }) {
  const module = getModule(moduleId)

  return (
    <PageContainer>
      <PageHeader
        title={module.label}
        description={module.summary}
        actions={
          <span className="rounded-full border border-border-strong bg-surface px-3 py-1 text-sm font-medium text-fg-muted shadow-raise">
            Đang phát triển
          </span>
        }
      />

      <div className="grid items-start gap-12 md:grid-cols-[minmax(0,1fr)_minmax(0,24rem)]">
        <div className="max-w-md space-y-4">
          <span
            className={cn(
              'flex size-12 items-center justify-center rounded-full shadow-raise',
              NOTE_PAPER[module.note],
              NOTE_INK[module.note],
            )}
          >
            {module.renderIcon(22)}
          </span>
          <h2 className="text-2xl font-extrabold tracking-tight text-fg">Phân hệ chưa được triển khai</h2>
          <p className="text-base text-fg-muted">
            Phân hệ này đã có trong thiết kế và sẽ được xây dựng ở giai đoạn tiếp theo. Chưa có dữ liệu nào được lưu.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link to="/chat" className={buttonClasses('primary', 'md')}>
              Trò chuyện với Atlas
            </Link>
            <Link to="/" className={buttonClasses('secondary', 'md')}>
              Về trang tổng quan
            </Link>
          </div>
        </div>

        {/* The plan, written on the module's own sticky note. */}
        <StickyNote color={module.note} tilt={-0.8}>
          <section aria-labelledby="planned-heading" className="p-6 pt-7">
            <h3 id="planned-heading" className={cn('text-lg font-extrabold', NOTE_INK[module.note])}>
              Chức năng dự kiến
            </h3>
            <ul className="mt-3 space-y-2.5">
              {module.capabilities.map((capability) => (
                <li key={capability} className="flex items-start gap-3 text-[0.9375rem] text-fg">
                  {/* An empty checkbox: planned, not done yet. */}
                  <span
                    aria-hidden="true"
                    className="mt-1 size-4 shrink-0 rounded border-2 border-current opacity-50"
                  />
                  {capability}
                </li>
              ))}
            </ul>
          </section>
        </StickyNote>
      </div>
    </PageContainer>
  )
}
