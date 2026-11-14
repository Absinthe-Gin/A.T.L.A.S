import { Link } from 'react-router'

export function NotFoundPage() {
  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold">Không tìm thấy trang</h1>
      <p className="text-slate-600">Đường dẫn bạn truy cập không tồn tại.</p>
      <Link to="/" className="font-medium text-blue-700 underline hover:text-blue-600">
        Về trang chủ
      </Link>
    </div>
  )
}
