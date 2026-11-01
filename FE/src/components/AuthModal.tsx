import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ArrowRight, Dumbbell, LockKeyhole, X } from 'lucide-react'
import { api, type User } from '../lib/api'

export type AuthMode = 'login' | 'register'

type Props = {
  mode: AuthMode
  onModeChange: (mode: AuthMode) => void
  onClose: () => void
  onSuccess: (user: User) => void
}

export default function AuthModal({ mode, onModeChange, onClose, onSuccess }: Props) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const emailRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    emailRef.current?.focus()
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  useEffect(() => {
    setError('')
  }, [mode])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    if (mode === 'register' && password !== confirmPassword) {
      setError('Mật khẩu xác nhận chưa khớp.')
      return
    }
    setSubmitting(true)
    try {
      const user = mode === 'register'
        ? await api.register(name.trim(), email.trim(), password)
        : await api.login(email.trim(), password)
      onSuccess(user)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không thể kết nối máy chủ.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
      <section className="auth-modal" role="dialog" aria-modal="true" aria-labelledby="auth-title">
        <button className="icon-button modal-close" type="button" onClick={onClose} aria-label="Đóng">
          <X size={20} />
        </button>
        <div className="auth-mark"><Dumbbell size={24} strokeWidth={2.5} /></div>
        <div className="auth-eyebrow">AI-4GYM ACCOUNT</div>
        <h2 id="auth-title">{mode === 'register' ? 'Bắt đầu hành trình của bạn.' : 'Chào mừng bạn trở lại.'}</h2>
        <p className="auth-description">
          {mode === 'register'
            ? 'Tạo tài khoản để lưu các cuộc trò chuyện và tiếp tục tập luyện bất cứ lúc nào.'
            : 'Đăng nhập để xem lại lịch sử và tiếp tục những cuộc trò chuyện trước.'}
        </p>
        <div className="auth-tabs" role="tablist" aria-label="Tài khoản">
          <button type="button" role="tab" aria-selected={mode === 'login'} className={mode === 'login' ? 'active' : ''} onClick={() => onModeChange('login')}>Đăng nhập</button>
          <button type="button" role="tab" aria-selected={mode === 'register'} className={mode === 'register' ? 'active' : ''} onClick={() => onModeChange('register')}>Đăng ký</button>
        </div>
        <form className="auth-form" onSubmit={submit}>
          {mode === 'register' && (
            <label>
              <span>Tên hiển thị</span>
              <input autoComplete="name" minLength={2} maxLength={80} required value={name} onChange={(event) => setName(event.target.value)} placeholder="Tên của bạn" />
            </label>
          )}
          <label>
            <span>Email</span>
            <input ref={emailRef} type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="ban@email.com" />
          </label>
          <label>
            <span>Mật khẩu</span>
            <input type="password" autoComplete={mode === 'register' ? 'new-password' : 'current-password'} minLength={mode === 'register' ? 8 : undefined} required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Ít nhất 8 ký tự" />
          </label>
          {mode === 'register' && (
            <label>
              <span>Xác nhận mật khẩu</span>
              <input type="password" autoComplete="new-password" required value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="Nhập lại mật khẩu" />
            </label>
          )}
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="auth-submit" type="submit" disabled={submitting}>
            <span>{submitting ? 'Đang xử lý...' : mode === 'register' ? 'Tạo tài khoản' : 'Đăng nhập'}</span>
            <ArrowRight size={18} />
          </button>
        </form>
        <p className="auth-footnote"><LockKeyhole size={14} /> Tài khoản được bảo vệ; lịch sử chỉ hiển thị với bạn.</p>
      </section>
    </div>
  )
}
