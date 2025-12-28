import { NextRequest, NextResponse } from 'next/server'

/**
 * Proxy endpoint for character CRUD operations
 * Forwards requests to backend API at localhost:8000
 */

export async function GET(request: NextRequest) {
  try {
    // Use API_URL for server-side (Docker: http://api:8000)
    // Falls back to localhost for local development
    const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    // Forward auth header from client
    const authHeader = request.headers.get('Authorization')
    
    console.log(`[API Route] Forwarding GET to: ${apiUrl}/api/characters`)
    
    const headers: HeadersInit = { 'Content-Type': 'application/json' }
    if (authHeader) {
      headers['Authorization'] = authHeader
    }
    
    const response = await fetch(`${apiUrl}/api/characters`, {
      method: 'GET',
      headers,
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      return NextResponse.json(
        { error: errorData.detail || 'Failed to fetch characters' },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error proxying character list:', error)
    return NextResponse.json(
      { error: 'Failed to connect to backend API' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Use API_URL for server-side (Docker: http://api:8000)
    // Falls back to localhost for local development
    const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    // Forward auth header from client
    const authHeader = request.headers.get('Authorization')
    
    console.log(`[API Route] Forwarding POST to: ${apiUrl}/api/characters`)
    console.log('[API Route] Body keys:', Object.keys(body))
    
    const headers: HeadersInit = { 'Content-Type': 'application/json' }
    if (authHeader) {
      headers['Authorization'] = authHeader
    }
    
    const response = await fetch(`${apiUrl}/api/characters`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      console.error('[API Route] Backend error:', errorData)
      return NextResponse.json(
        { error: errorData.detail || 'Failed to create character' },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    console.log('[API Route] Character created successfully, ID:', data.id)
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error proxying character creation:', error)
    return NextResponse.json(
      { error: 'Failed to connect to backend API' },
      { status: 500 }
    )
  }
}
