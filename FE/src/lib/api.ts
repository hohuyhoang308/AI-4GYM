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

const API_PREFIX = import.meta.env.DEV ? '/api' : ''

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_PREFIX}${path}`, {
    credentials: 'include',
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init.headers,
    },
  })
  if (!response.ok) {
    let detail = `Có lỗi xảy ra (${response.status})`
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // Keep the HTTP status if the response body is not JSON.
    }
    throw new Error(detail)
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
  chat: (message: string, session_id?: string | null, conversation_id?: string | null) =>
    request<ChatReply>('/chat', { method: 'POST', body: JSON.stringify({ message, session_id, conversation_id }) }),
}
