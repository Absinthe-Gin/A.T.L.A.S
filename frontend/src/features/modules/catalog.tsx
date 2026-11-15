import type { ReactNode } from 'react'

import {
  IconChat,
  IconDashboard,
  IconMemory,
  IconPlane,
  IconUtensils,
  IconWallet,
} from '@/components/icons'

/**
 * Every area of the product, with its real implementation status.
 * Navigation, the dashboard and placeholder pages all read from this list,
 * so a module's status is stated in exactly one place.
 */

export type ModuleId = 'dashboard' | 'chat' | 'finance' | 'travel' | 'food' | 'memory'

/** `available`: usable now. `planned`: designed, not implemented yet. */
export type ModuleStatus = 'available' | 'planned'

/** The sticky-note colour that identifies a module everywhere it appears. */
export type NoteColor = 'yellow' | 'peach' | 'green' | 'pink' | 'blue'

export interface AppModule {
  id: ModuleId
  path: string
  label: string
  summary: string
  /** What the module will do once implemented (from CLAUDE.md, section 1.1). */
  capabilities: string[]
  status: ModuleStatus
  note: NoteColor
  renderIcon: (size?: number) => ReactNode
}

export const MODULES: readonly AppModule[] = [
  {
    id: 'dashboard',
    path: '/',
    label: 'Tổng quan',
    summary: 'Trạng thái hệ thống và lối vào các phân hệ.',
    capabilities: ['Tổng hợp thông tin cá nhân', 'Báo cáo tài chính', 'Kế hoạch du lịch sắp tới'],
    status: 'available',
    note: 'yellow',
    renderIcon: (size) => <IconDashboard size={size} />,
  },
  {
    id: 'chat',
    path: '/chat',
    label: 'Trợ lý AI',
    summary: 'Trò chuyện với trợ lý bằng ngôn ngữ tự nhiên.',
    capabilities: ['Hiểu yêu cầu bằng tiếng Việt', 'Ghi nhớ ngữ cảnh hội thoại', 'Điều phối các phân hệ'],
    status: 'available',
    note: 'blue',
    renderIcon: (size) => <IconChat size={size} />,
  },
  {
    id: 'finance',
    path: '/finance',
    label: 'Tài chính',
    summary: 'Quản lý thu chi, ngân sách và báo cáo tài chính cá nhân.',
    capabilities: ['Ghi nhận thu nhập và chi tiêu', 'Danh mục giao dịch', 'Ngân sách theo kỳ', 'Báo cáo và phân tích'],
    status: 'available',
    note: 'green',
    renderIcon: (size) => <IconWallet size={size} />,
  },
  {
    id: 'travel',
    path: '/travel',
    label: 'Du lịch',
    summary: 'Kế hoạch chuyến đi, bản đồ, thời tiết và cách đi tới nơi.',
    capabilities: ['Kế hoạch và lịch trình chuyến đi', 'Tìm địa điểm trên bản đồ', 'Thời tiết theo thời gian thực', 'Cách đi bằng máy bay, tàu, xe'],
    status: 'available',
    note: 'yellow',
    renderIcon: (size) => <IconPlane size={size} />,
  },
  {
    id: 'food',
    path: '/food',
    label: 'Ẩm thực',
    summary: 'Món đặc sản theo khu vực và quán ăn gần bạn.',
    capabilities: ['Món đặc sản theo khu vực', 'Tìm quán theo món ăn', 'Khoảng cách và vị trí trên bản đồ'],
    status: 'available',
    note: 'peach',
    renderIcon: (size) => <IconUtensils size={size} />,
  },
  {
    id: 'memory',
    path: '/memory',
    label: 'Ghi nhớ',
    summary: 'Thông tin cá nhân trợ lý được phép ghi nhớ.',
    capabilities: ['Xem lịch sử hội thoại', 'Xem và sửa thông tin đã ghi nhớ', 'Xóa thông tin không muốn lưu'],
    status: 'planned',
    note: 'pink',
    renderIcon: (size) => <IconMemory size={size} />,
  },
]

export function getModule(id: ModuleId): AppModule {
  const found = MODULES.find((module) => module.id === id)
  if (!found) {
    throw new Error(`Unknown module: ${id}`)
  }
  return found
}
