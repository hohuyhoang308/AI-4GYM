import { useEffect, useRef, type KeyboardEvent } from 'react'
import { ArrowUp, LockKeyhole, Sparkles } from 'lucide-react'

type Props = {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  busy: boolean
  guest: boolean
}

export default function Composer({ value, onChange, onSubmit, busy, guest }: Props) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, 170)}px`
  }, [value])

  function keyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      onSubmit()
    }
  }

  return (
    <div className="composer-outer">
      <div className="composer-wrap">
        <div className="composer-box">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={keyDown}
            placeholder="Hỏi về bài tập, nhóm cơ hoặc lịch tập của bạn..."
            rows={1}
            maxLength={1000}
            disabled={busy}
            aria-label="Nhập câu hỏi"
          />
          <div className="composer-bottom">
            <span className="composer-hint"><Sparkles size={14} /> Hỏi bằng tiếng Việt tự nhiên</span>
            <button type="button" className="send-button" onClick={onSubmit} disabled={busy || !value.trim()} aria-label="Gửi câu hỏi">
              <ArrowUp size={19} strokeWidth={2.5} />
            </button>
          </div>
        </div>
        <p className="composer-note">
          {guest ? <><LockKeyhole size={13} /> Chế độ khách: hội thoại sẽ mất khi tải lại trang.</> : 'Câu trả lời chỉ mang tính tham khảo. Hãy ưu tiên kỹ thuật và mức tập phù hợp với bạn.'}
        </p>
      </div>
    </div>
  )
}
