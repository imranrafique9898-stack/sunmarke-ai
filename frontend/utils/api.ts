import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface QueryRequest {
  query: string
  transcribed_text?: string
}

export interface RAGContext {
  context: string
  sources: string[]
  chunks_count: number
}

export interface QueryResponse {
  query: string
  rag: RAGContext
  responses: {
    gemini: string
    groq?: string
    deepseek?: string
  }
  response_time_ms: number
}

export interface ApiStats {
  documents: number
  chunks: number
  queries_processed: number
  status: string
}

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 60000, // 60 second timeout for LLM responses
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 503) {
      throw new Error('Backend unavailable. Make sure the backend server is running at ' + API_URL)
    }
    if (error.message === 'Network Error') {
      throw new Error('Network error. Check if backend is running at ' + API_URL)
    }
    throw error
  }
)

export const healthCheck = async (): Promise<void> => {
  const response = await apiClient.get('/health')
  return response.data
}

export const queryBackend = async (query: string): Promise<QueryResponse> => {
  const response = await apiClient.post<QueryResponse>('/api/query', {
    query: query,
    transcribed_text: query,
  })
  return response.data
}

export const initializeEmbeddings = async (): Promise<{ message: string }> => {
  const response = await apiClient.post('/api/initialize')
  return response.data
}

export const getStats = async (): Promise<ApiStats> => {
  const response = await apiClient.get<ApiStats>('/api/stats')
  return response.data
}

export default apiClient

export interface StreamToken {
  model: 'groq1' | 'groq2'
  token: string
  done: boolean
}

export async function streamQuery(
  query: string,
  onToken: (model: 'groq1' | 'groq2', token: string, done: boolean) => void
): Promise<void> {
  const response = await fetch(`${API_URL}/api/query/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, transcribed_text: query }),
  })

  if (!response.ok) throw new Error(`Stream error: ${response.status}`)
  if (!response.body) throw new Error('No response body')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.trim()) continue
      try {
        const parsed: StreamToken = JSON.parse(line)
        onToken(parsed.model, parsed.token, parsed.done)
      } catch {}
    }
  }
}
