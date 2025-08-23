// NextAuth route temporarily disabled for deployment
// See route.ts.disabled for full implementation

export async function GET() {
  return Response.json({ 
    message: "Authentication service temporarily unavailable",
    status: "maintenance" 
  });
}

export async function POST() {
  return Response.json({ 
    message: "Authentication service temporarily unavailable",
    status: "maintenance" 
  });
}
