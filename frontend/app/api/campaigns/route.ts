import { NextRequest, NextResponse } from 'next/server'

/**
 * Proxy endpoint for campaign operations
 * Forwards requests to backend API
 */

export async function GET(request: NextRequest) {
    try {
        // Use API_URL for server-side (Docker: http://api:8000)
        // Falls back to localhost for local development
        const apiUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        console.log(`[API Route] Forwarding GET to: ${apiUrl}/api/campaigns`)

        // Forward auth header if present
        const authHeader = request.headers.get('authorization')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (authHeader) {
            headers['Authorization'] = authHeader
        }

        const response = await fetch(`${apiUrl}/api/campaigns`, {
            method: 'GET',
            headers,
        })

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
        console.error('Error proxying campaign list:', error)
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

        console.log(`[API Route] Forwarding POST to: ${apiUrl}/api/campaigns`)

        // Forward auth header if present
        const authHeader = request.headers.get('authorization')
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
        })

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
        console.error('Error proxying campaign creation:', error)
        return NextResponse.json(
            { error: 'Failed to connect to backend API' },
            { status: 500 }
        )
    }
}
