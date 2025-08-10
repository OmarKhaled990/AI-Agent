// frontend/app/api/backend/[...path]/route.ts
import { NextRequest } from 'next/server'

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function GET(req: NextRequest, { params }: { params: { path: string[] } }) {
  const url = `${BACKEND}/${params.path.join('/')}${req.nextUrl.search}`
  const r = await fetch(url)
  const text = await r.text()
  return new Response(text, { status: r.status, headers: { 'Content-Type': r.headers.get('Content-Type') || 'application/json' } })
}

export async function POST(req: NextRequest, { params }: { params: { path: string[] } }) {
  const url = `${BACKEND}/${params.path.join('/')}${req.nextUrl.search}`
  const body = await req.text()
  const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': req.headers.get('Content-Type') || 'application/json' }, body })
  const text = await r.text()
  return new Response(text, { status: r.status, headers: { 'Content-Type': r.headers.get('Content-Type') || 'application/json' } })
}