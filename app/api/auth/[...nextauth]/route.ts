// NextAuth route temporarily disabled for deployment
// See route.ts.disabled for full implementation

import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({ 
    message: "Authentication service temporarily unavailable",
    status: "maintenance" 
  });
}

export async function POST() {
  return NextResponse.json({ 
    message: "Authentication service temporarily unavailable",
    status: "maintenance" 
  });
}
