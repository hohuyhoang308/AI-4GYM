import { useCallback, useEffect, useRef, useState } from 'react'
import { Activity, ArrowRight, BookOpenText, CalendarDays, ChevronRight, Dumbbell, Menu, MessageCircleMore, ShieldCheck, Sparkles, X } from 'lucide-react'
import AuthModal, { type AuthMode } from './components/AuthModal'
import Composer from './components/Composer'
import MessageBubble from './components/MessageBubble'
import Sidebar from './components/Sidebar'
import { api, type ChatMessage, type Conversation, type Health, type User } from './lib/api'

const suggestions = [
  { icon: Dumbbell, label: 'Kỹ thuật bài tập', prompt: 'Hướng dẫn squat đúng kỹ thuật và những lỗi cần tránh', tone: 'orange' },
  { icon: CalendarDays, label: 'Lịch tập của tôi', prompt: 'Gợi ý lịch tập gym 3 buổi/tuần cho người mới', tone: 'green' },
  { icon: Activity, label: 'Tập theo nhóm cơ', prompt: 'Gợi ý những bài tập hiệu quả cho cơ ngực', tone: 'purple' },
  { icon: BookOpenText, label: 'Kiến thức cơ bản', prompt: 'Tại sao cần khởi động trước khi tập gym?', tone: 'blue' },
]

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [booting, setBooting] = useState(true)
  const [health, setHealth] = useState<Health | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [guestSessionId, setGuestSessionId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [pending, setPending] = useState(false)
  const [loadingConversation, setLoadingConversation] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [authOpen, setAuthOpen] = useState(false)
  const [authMode, setAuthMode] = useState<AuthMode>('login')
  const [toast, setToast] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let alive = true
    async function bootstrap() {
      try {
        const state = await api.health()
        if (alive) setHealth(state)
      } catch {
        if (alive) setHealth(null)
      }
      try {
        const me = await api.me()
        if (!alive) return
        setUser(me)
        const list = await api.conversations()
        if (!alive) return
        setConversations(list)
        if (list.length > 0) {
          const detail = await api.conversation(list[0].id)
          if (alive) {
            setActiveId(detail.id)
            setMessages(detail.messages)
          }
        }
      } catch {
        // An unauthenticated visitor starts in guest mode.
      } finally {
        if (alive) setBooting(false)
      }
    }
    void bootstrap()
    const refresh = window.setInterval(() => { void api.health().then(setHealth).catch(() => setHealth(null)) }, 60_000)
    return () => { alive = false; window.clearInterval(refresh) }
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, pending])

  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(''), 4200)
    return () => window.clearTimeout(timer)
  }, [toast])

  const closeAuth = useCallback(() => setAuthOpen(false), [])

  function openAuth(mode: AuthMode = 'login') {
    if (pending) return
    setAuthMode(mode)
    setAuthOpen(true)
    setSidebarOpen(false)
  }

  function newChat() {
    if (pending) return
    setActiveId(null)
    setMessages([])
    setGuestSessionId(null)
    setInput('')
    setSidebarOpen(false)
  }

  async function selectConversation(id: string) {
    if (pending || id === activeId) {
      setSidebarOpen(false)
      return
    }
    setLoadingConversation(true)
    try {
      const detail = await api.conversation(id)
      setActiveId(id)
      setMessages(detail.messages)
      setGuestSessionId(null)
      setSidebarOpen(false)
    } catch (cause) {
      setToast(cause instanceof Error ? cause.message : 'Không thể mở hội thoại.')
    } finally {
      setLoadingConversation(false)
    }
  }

  async function renameConversation(id: string, title: string) {
    try {
      const updated = await api.renameConversation(id, title)
      setConversations((items) => items.map((item) => item.id === id ? updated : item))
    } catch (cause) {
      setToast(cause instanceof Error ? cause.message : 'Không thể đổi tên.')
    }
  }

  async function deleteConversation(id: string) {
    if (!window.confirm('Xóa cuộc trò chuyện này? Bạn sẽ không thể khôi phục.')) return
    try {
      await api.deleteConversation(id)
      setConversations((items) => items.filter((item) => item.id !== id))
      if (activeId === id) newChat()
    } catch (cause) {
      setToast(cause instanceof Error ? cause.message : 'Không thể xóa hội thoại.')
    }
  }

  async function authSuccess(nextUser: User) {
    setUser(nextUser)
    setAuthOpen(false)
    setMessages([])
    setActiveId(null)
    setGuestSessionId(null)
    setInput('')
    try {
      const list = await api.conversations()
      setConversations(list)
      if (list.length > 0) {
        const detail = await api.conversation(list[0].id)
        setActiveId(detail.id)
        setMessages(detail.messages)
      }
    } catch (cause) {
      setToast(cause instanceof Error ? cause.message : 'Không thể tải lịch sử.')
    }
  }

  async function logout() {
    if (pending) return
    try {
      await api.logout()
      setUser(null)
      setConversations([])
      newChat()
    } catch (cause) {
      setToast(cause instanceof Error ? cause.message : 'Không thể đăng xuất.')
    }
  }

  async function sendMessage(value = input) {
    const message = value.trim()
    if (!message || pending || booting || loadingConversation) return
    const optimisticId = crypto.randomUUID()
    setMessages((items) => [...items, { id: optimisticId, role: 'user', content: message, sources: [] }])
    setInput('')
    setPending(true)
    try {
      const reply = await api.chat(message, user ? null : guestSessionId, user ? activeId : null)
      setMessages((items) => [...items, { id: crypto.randomUUID(), role: 'assistant', content: reply.answer, sources: reply.sources }])
      if (user && reply.conversation_id) {
        setActiveId(reply.conversation_id)
        try {
          setConversations(await api.conversations())
        } catch {
          setToast('Đã lưu câu trả lời, nhưng chưa cập nhật được danh sách hội thoại.')
        }
      } else {
        setGuestSessionId(reply.session_id)
      }
    } catch (cause) {
      setMessages((items) => items.filter((item) => item.id !== optimisticId))
      setInput(message)
      setToast(cause instanceof Error ? cause.message : 'Không thể gửi câu hỏi. Hãy thử lại.')
    } finally {
      setPending(false)
    }
  }

  const currentTitle = conversations.find((item) => item.id === activeId)?.title ?? 'Cuộc trò chuyện mới'
  const ready = health?.status === 'ready'

  return (
    <div className="app-shell">
      <Sidebar
        user={user}
        conversations={conversations}
        activeId={activeId}
        open={sidebarOpen}
        busy={pending || loadingConversation}
        onClose={() => setSidebarOpen(false)}
        onNew={newChat}
        onSelect={(id) => void selectConversation(id)}
        onRename={renameConversation}
        onDelete={deleteConversation}
        onAuth={() => openAuth('login')}
        onLogout={() => void logout()}
      />

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button type="button" className="icon-button mobile-menu" onClick={() => setSidebarOpen(true)} aria-label="Mở thanh bên"><Menu size={21} /></button>
            <div className="topbar-path"><span>AI-4GYM</span><ChevronRight size={14} /><strong>{currentTitle}</strong></div>
          </div>
          <div className="topbar-right">
            <div className={`status-pill ${ready ? 'online' : 'offline'}`}><span className="status-dot" /> {ready ? 'AI sẵn sàng' : 'Đang kết nối'}</div>
            {!user && !booting && <button type="button" className="topbar-login" onClick={() => openAuth('login')}>Đăng nhập <ArrowRight size={15} /></button>}
          </div>
        </header>

        <div className="conversation-scroll">
          {loadingConversation ? (
            <div className="loading-conversation"><span className="spinner" /> Đang mở cuộc trò chuyện...</div>
          ) : messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-inner">
                <div className="welcome-kicker"><span className="welcome-kicker-icon"><Sparkles size={15} /></span> TRỢ LÝ TẬP LUYỆN CỦA BẠN</div>
                <h1>Tập đúng hôm nay.<br /><em>Tiến bộ mỗi ngày.</em></h1>
                <p className="welcome-subtitle">Hỏi bất cứ điều gì về bài tập Gym, kỹ thuật an toàn hoặc lịch tập phù hợp với thời gian của bạn.</p>
                <div className="suggestions-heading"><span>BẮT ĐẦU VỚI MỘT CÂU HỎI</span><span className="suggestions-line" /></div>
                <div className="suggestion-grid">
                  {suggestions.map(({ icon: Icon, label, prompt, tone }) => (
                    <button type="button" className="suggestion-card" key={label} onClick={() => void sendMessage(prompt)} disabled={booting || pending}>
                      <span className={`suggestion-icon ${tone}`}><Icon size={20} strokeWidth={2} /></span>
                      <span className="suggestion-copy"><strong>{label}</strong><small>{prompt}</small></span>
                      <ArrowRight size={17} className="suggestion-arrow" />
                    </button>
                  ))}
                </div>
                <div className="welcome-assurance"><ShieldCheck size={16} /> Câu trả lời dựa trên dữ liệu Gym local; hãy kiểm tra kỹ thuật và chọn mức tập phù hợp.</div>
              </div>
            </div>
          ) : (
            <div className="chat-thread">
              <div className="thread-intro"><span><MessageCircleMore size={16} /></span> Hãy hỏi tiếp bất cứ lúc nào — mình vẫn theo mạch hội thoại này.</div>
              {messages.map((message) => <MessageBubble key={message.id} message={message} />)}
              {pending && (
                <div className="message-row assistant-row">
                  <div className="assistant-avatar"><Dumbbell size={17} strokeWidth={2.6} /></div>
                  <div className="thinking-indicator"><span className="typing-dots"><i /><i /><i /></span> Đang tìm thông tin phù hợp...</div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <Composer value={input} onChange={setInput} onSubmit={() => void sendMessage()} busy={pending || booting || loadingConversation} guest={!user} />
      </main>

      {toast && <div className="toast" role="alert"><span>{toast}</span><button type="button" onClick={() => setToast('')} aria-label="Đóng thông báo"><X size={16} /></button></div>}
      {authOpen && <AuthModal mode={authMode} onModeChange={setAuthMode} onClose={closeAuth} onSuccess={(nextUser) => void authSuccess(nextUser)} />}
    </div>
  )
}

export default App
