export type User = {
  id: number
  email: string
  display_name: string
  created_at: string
}

export type Source = {
  id: string
  title: string
  source: string
  excel_row?: number | null
  kind: string
  score: number
}

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources: Source[]
  created_at?: string
}

export type Conversation = {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export type ConversationDetail = Conversation & { messages: ChatMessage[] }

export type ChatReply = {
  session_id: string
  conversation_id: string | null
  answer: string
  sources: Source[]
  refused: boolean
}

export type Health = {
  status: 'ready' | 'setup_required'
  ollama_running: boolean
  chat_model_ready: boolean
  embed_model_ready: boolean
  indexed_documents: number
  database_running: boolean
}

export function safeUUID(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
  })
}

const API_PREFIX = import.meta.env.DEV ? '/api' : ''

// Mô hình local có thể mất 1–2 phút cho một câu RAG; quá thời gian này coi như lỗi mạng.
export const CHAT_TIMEOUT_MS = 5 * 60 * 1000
const DEFAULT_TIMEOUT_MS = 30 * 1000

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<T> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  let response: Response
  try {
    response = await fetch(`${API_PREFIX}${path}`, {
      credentials: 'include',
      ...init,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...init.headers,
      },
    })
  } catch (cause) {
    // status 0: lỗi mạng hoặc quá thời gian chờ, có thể gửi lại cùng request_id.
    const timedOut = cause instanceof DOMException && cause.name === 'AbortError'
    throw new ApiError(timedOut ? 'Máy chủ phản hồi quá lâu. Bạn có thể gửi lại câu hỏi.' : 'Không kết nối được máy chủ. Kiểm tra backend rồi gửi lại.', 0)
  } finally {
    window.clearTimeout(timer)
  }
  if (!response.ok) {
    // Cookie phiên là HttpOnly nên JavaScript không xóa được; backend tự gửi lệnh xóa kèm 401.
    let detail = `Có lỗi xảy ra (${response.status})`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // Keep the HTTP status if the response body is not JSON.
    }
    throw new ApiError(detail, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  health: () => request<Health>('/health'),
  me: () => request<User>('/auth/me'),
  register: (display_name: string, email: string, password: string) =>
    request<User>('/auth/register', { method: 'POST', body: JSON.stringify({ display_name, email, password }) }),
  login: (email: string, password: string) =>
    request<User>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  logout: () => request<{ ok: boolean }>('/auth/logout', { method: 'POST' }),
  conversations: () => request<Conversation[]>('/conversations'),
  conversation: (id: string) => request<ConversationDetail>(`/conversations/${encodeURIComponent(id)}`),
  renameConversation: (id: string, title: string) => request<Conversation>(`/conversations/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify({ title }) }),
  deleteConversation: (id: string) => request<void>(`/conversations/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  // request_id do nơi gọi giữ lại: gửi lại cùng câu hỏi sau lỗi mạng sẽ dùng lại id cũ,
  // backend trả kết quả đã lưu thay vì tạo thêm tin nhắn.
  chat: (message: string, request_id: string, session_id?: string | null, conversation_id?: string | null) =>
    request<ChatReply>('/chat', { method: 'POST', body: JSON.stringify({ message, session_id, conversation_id, request_id }) }, CHAT_TIMEOUT_MS),
}
