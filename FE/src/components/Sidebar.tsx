import { useState, type FormEvent } from 'react'
import { ArrowUpRight, Dumbbell, LogOut, MessageSquareText, MoreHorizontal, Plus, Search, Trash2, X, Pencil } from 'lucide-react'
import type { Conversation, User } from '../lib/api'

type Props = {
  user: User | null
  conversations: Conversation[]
  activeId: string | null
  open: boolean
  busy: boolean
  onClose: () => void
  onNew: () => void
  onSelect: (id: string) => void
  onRename: (id: string, title: string) => Promise<void>
  onDelete: (id: string) => Promise<void>
  onAuth: () => void
  onLogout: () => void
}

function timeLabel(value: string): string {
  const date = new Date(value)
  const now = new Date()
  if (date.toDateString() === now.toDateString()) return 'Hôm nay'
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) return 'Hôm qua'
  return date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })
}

export default function Sidebar({ user, conversations, activeId, open, busy, onClose, onNew, onSelect, onRename, onDelete, onAuth, onLogout }: Props) {
  const [search, setSearch] = useState('')
  const [menuId, setMenuId] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')
  const visibleConversations = conversations.filter((item) => item.title.toLocaleLowerCase('vi').includes(search.toLocaleLowerCase('vi')))

  async function submitRename(event: FormEvent<HTMLFormElement>, id: string) {
    event.preventDefault()
    if (editingTitle.trim()) await onRename(id, editingTitle.trim())
    setEditingId(null)
  }

  return (
    <>
      {open && <button type="button" className="sidebar-scrim" onClick={onClose} aria-label="Đóng thanh bên" />}
      <aside className={`sidebar ${open ? 'sidebar-open' : ''}`} aria-label="Thanh điều hướng">
        <div className="sidebar-top">
          <div className="brand-row">
            <div className="brand-icon"><Dumbbell size={20} strokeWidth={2.8} /></div>
            <div className="brand-text"><strong>AI-4GYM</strong><span>YOUR FITNESS COMPANION</span></div>
            <button type="button" className="icon-button sidebar-close" onClick={onClose} aria-label="Đóng"><X size={19} /></button>
          </div>
          <button className="new-chat-button" type="button" onClick={onNew} disabled={busy}>
            <Plus size={18} strokeWidth={2.4} /> Cuộc trò chuyện mới
          </button>
        </div>

        <div className="sidebar-middle">
          <div className="sidebar-section-heading"><span>LỊCH SỬ TRÒ CHUYỆN</span><span className="history-count">{user ? conversations.length : '—'}</span></div>
          {user ? (
            <>
              <label className="history-search">
                <Search size={16} />
                <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Tìm cuộc trò chuyện..." aria-label="Tìm cuộc trò chuyện" />
              </label>
              <div className="history-list">
                {visibleConversations.length === 0 ? (
                  <p className="history-empty">{search ? 'Không tìm thấy cuộc trò chuyện.' : 'Cuộc trò chuyện đầu tiên sẽ hiện ở đây.'}</p>
                ) : visibleConversations.map((item) => (
                  <div key={item.id} className={`history-item ${activeId === item.id ? 'selected' : ''}`}>
                    {editingId === item.id ? (
                      <form className="history-rename" onSubmit={(event) => void submitRename(event, item.id)}>
                        <input autoFocus value={editingTitle} onChange={(event) => setEditingTitle(event.target.value)} maxLength={120} onKeyDown={(event) => { if (event.key === 'Escape') setEditingId(null) }} aria-label="Tên hội thoại mới" />
                      </form>
                    ) : (
                      <button type="button" className="history-select" onClick={() => onSelect(item.id)} disabled={busy}>
                        <MessageSquareText size={17} />
                        <span className="history-title">{item.title}</span>
                      </button>
                    )}
                    {editingId !== item.id && (
                      <div className="history-actions">
                        <button type="button" className="history-more" aria-label={`Tùy chọn ${item.title}`} onClick={() => setMenuId(menuId === item.id ? null : item.id)}><MoreHorizontal size={18} /></button>
                        {menuId === item.id && (
                          <div className="history-menu">
                            <div className="history-menu-date">{timeLabel(item.updated_at)}</div>
                            <button type="button" onClick={() => { setEditingId(item.id); setEditingTitle(item.title); setMenuId(null) }}><Pencil size={14} /> Đổi tên</button>
                            <button type="button" className="danger" onClick={() => { setMenuId(null); void onDelete(item.id) }}><Trash2 size={14} /> Xóa hội thoại</button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="guest-history">
              <div className="guest-history-icon"><MessageSquareText size={19} /></div>
              <strong>Lịch sử của bạn</strong>
              <p>Đăng nhập để lưu và xem lại các cuộc trò chuyện trên máy này.</p>
              <button type="button" onClick={onAuth}>Đăng nhập ngay <ArrowUpRight size={15} /></button>
            </div>
          )}
        </div>

        <div className="sidebar-bottom">
          <div className="sidebar-bottom-label"><span className="sidebar-bottom-dot" /> Tập luyện thông minh hơn mỗi ngày</div>
          {user ? (
            <div className="account-row">
              <div className="account-avatar">{user.display_name.trim().charAt(0).toUpperCase()}</div>
              <div className="account-copy"><strong>{user.display_name}</strong><span>{user.email}</span></div>
              <button className="account-logout" type="button" onClick={onLogout} aria-label="Đăng xuất" title="Đăng xuất"><LogOut size={18} /></button>
            </div>
          ) : (
            <button type="button" className="guest-account" onClick={onAuth}>
              <div className="account-avatar guest-avatar">G</div>
              <div className="account-copy"><strong>Chế độ khách</strong><span>Lịch sử không được lưu</span></div>
              <ArrowUpRight size={17} />
            </button>
          )}
        </div>
      </aside>
    </>
  )
}
