import { NextRequest, NextResponse } from 'next/server'

const FETCH_TIMEOUT_MS = 10000 // 10 seconds

/**
 * Proxy endpoint for campaign operations
 * Forwards requests to backend API
 */

export async function GET(request: NextRequest) {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)

    try {
        // Use API_URL for server-side (Docker: http://api:8000)
        // Falls back to localhost for local development
        const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        console.log(`[API Route] Forwarding GET to: ${apiUrl}/api/campaigns`)

        // Forward auth header if present
        const authHeader = request.headers.get('Authorization')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (authHeader) {
            headers['Authorization'] = authHeader
        }

        const response = await fetch(`${apiUrl}/api/campaigns`, {
            method: 'GET',
            headers,
            signal: controller.signal,
        })
        clearTimeout(timeoutId)

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
            return NextResponse.json(
                { error: errorData.detail || 'Failed to fetch campaigns' },
                { status: response.status }
            )
        }

        const data = await response.json()
        return NextResponse.json(data)
    } catch (error) {
        clearTimeout(timeoutId)
        console.error('Error proxying campaign list:', error)
        const message = error instanceof Error && error.name === 'AbortError'
            ? 'Request timed out'
            : 'Failed to connect to backend API'
        return NextResponse.json(
            { error: message },
            { status: 504 }
        )
    }
}

export async function POST(request: NextRequest) {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS)

    try {
        const body = await request.json()

        // Use API_URL for server-side (Docker: http://api:8000)
        // Falls back to localhost for local development
        const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        console.log(`[API Route] Forwarding POST to: ${apiUrl}/api/campaigns`)

        // Forward auth header if present
        const authHeader = request.headers.get('Authorization')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (authHeader) {
            headers['Authorization'] = authHeader
        }

        const response = await fetch(`${apiUrl}/api/campaigns`, {
            method: 'POST',
            headers,
            body: JSON.stringify(body),
            signal: controller.signal,
        })
        clearTimeout(timeoutId)

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
            console.error('[API Route] Backend error:', errorData)
            return NextResponse.json(
                { error: errorData.detail || 'Failed to create campaign' },
                { status: response.status }
            )
        }

        const data = await response.json()
        console.log('[API Route] Campaign created successfully, ID:', data.id)
        return NextResponse.json(data)
    } catch (error) {
        clearTimeout(timeoutId)
        console.error('Error proxying campaign creation:', error)
        const message = error instanceof Error && error.name === 'AbortError'
            ? 'Request timed out'
            : 'Failed to connect to backend API'
        return NextResponse.json(
            { error: message },
            { status: 504 }
        )
    }
}
