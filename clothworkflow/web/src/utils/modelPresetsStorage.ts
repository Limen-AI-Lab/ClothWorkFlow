import type { ModelPreset, UploadedImage } from '../studio/types'

const DB_NAME = 'clothworkflow-studio-v1'
const STORE = 'modelPresets'
const VERSION = 1

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, VERSION)
    req.onerror = () => reject(req.error ?? new Error('IndexedDB open failed'))
    req.onsuccess = () => resolve(req.result)
    req.onupgradeneeded = (ev) => {
      const db = (ev.target as IDBOpenDBRequest).result
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: 'id' })
      }
    }
  })
}

export async function listModelPresets(): Promise<ModelPreset[]> {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, 'readonly')
    const req = tx.objectStore(STORE).getAll()
    req.onsuccess = () => {
      const rows = (req.result as ModelPreset[]) || []
      resolve(rows.sort((a, b) => b.createdAt - a.createdAt))
    }
    req.onerror = () => reject(req.error ?? new Error('list failed'))
  })
}

export async function addModelPreset(input: {
  name: string
  image: UploadedImage
}): Promise<ModelPreset> {
  const id = `mp-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
  const record: ModelPreset = {
    id,
    name: input.name.trim() || '未命名模特',
    createdAt: Date.now(),
    mimeType: input.image.mimeType,
    base64Data: input.image.base64Data,
  }
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite')
    tx.objectStore(STORE).put(record)
    tx.oncomplete = () => resolve(record)
    tx.onerror = () => reject(tx.error ?? new Error('put failed'))
  })
}

export async function deleteModelPreset(id: string): Promise<void> {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite')
    tx.objectStore(STORE).delete(id)
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error ?? new Error('delete failed'))
  })
}
