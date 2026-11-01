import { useState } from 'react'
import { BookOpenText, Check, Copy, Dumbbell, ExternalLink } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ChatMessage, Source } from '../lib/api'

function SourceList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) return null
  return (
    <details className="sources-panel">
      <summary><BookOpenText size={15} /> {sources.length} nguồn tham khảo</summary>
      <div className="sources-content">
        {sources.map((source, index) => {
          const external = /^https?:\/\//.test(source.source)
          const label = source.kind === 'plan'
            ? 'Hướng dẫn lịch tập'
            : source.kind === 'exercise'
              ? 'Thư viện bài tập'
              : `Dữ liệu câu hỏi${source.excel_row ? ` · dòng ${source.excel_row}` : ''}`
          return external ? (
            <a key={`${source.id}-${index}`} href={source.source} target="_blank" rel="noopener noreferrer" className="source-item">
              <span className="source-item-mark">{index + 1}</span>
              <span className="source-item-copy"><strong>{source.title}</strong><small>{label}</small></span>
              <ExternalLink size={14} />
            </a>
          ) : (
            <div key={`${source.id}-${index}`} className="source-item">
              <span className="source-item-mark">{index + 1}</span>
              <span className="source-item-copy"><strong>{source.title}</strong><small>{label}</small></span>
            </div>
          )
        })}
      </div>
    </details>
  )
}

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const [copied, setCopied] = useState(false)
  if (message.role === 'user') {
    return (
      <div className="message-row user-row">
        <div className="user-bubble">{message.content}</div>
      </div>
    )
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      // Clipboard permission may be unavailable in some browsers.
    }
  }

  return (
    <div className="message-row assistant-row">
      <div className="assistant-avatar"><Dumbbell size={17} strokeWidth={2.6} /></div>
      <div className="assistant-message">
        <div className="assistant-label">AI-4GYM <span>TRỢ LÝ TẬP LUYỆN</span></div>
        <div className="markdown-body">
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
            a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>,
          }}>{message.content}</ReactMarkdown>
        </div>
        <div className="assistant-actions">
          <SourceList sources={message.sources} />
          <button type="button" className="copy-button" onClick={() => void copy()} aria-label="Sao chép câu trả lời" title="Sao chép câu trả lời">
            {copied ? <Check size={15} /> : <Copy size={15} />}
            <span>{copied ? 'Đã sao chép' : 'Sao chép'}</span>
          </button>
        </div>
      </div>
    </div>
  )
}
