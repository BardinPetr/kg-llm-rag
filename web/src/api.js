const API_BASE = '/api'

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/documents`)
  if (!res.ok) throw new Error('Failed to fetch documents')
  return res.json()
}

export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append('file', file)
  
  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) throw new Error('Failed to upload document')
  return res.json()
}

export async function fetchGraph() {
  const res = await fetch(`${API_BASE}/graph`)
  if (!res.ok) throw new Error('Failed to fetch graph')
  return res.json()
}

export async function fetchNode(uid) {
  const res = await fetch(`${API_BASE}/nodes/${uid}`)
  if (!res.ok) throw new Error('Failed to fetch node')
  return res.json()
}

export async function submitSearch(query) {
  const res = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  })
  if (!res.ok) throw new Error('Failed to submit search')
  return res.json()
}

export async function clearDatabase() {
  const res = await fetch(`${API_BASE}/clear`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to clear database')
  return res.json()
}
