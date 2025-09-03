"use client";
import { useState } from 'react';

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setStatus("sending");
    setError(null);
    try {
      const res = await fetch('/api/auth/signin/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, callbackUrl: '/dashboard' })
      });
      if (!res.ok) throw new Error('Failed to request magic link');
      setStatus("sent");
    } catch (err) {
      setError(err.message || 'Error');
      setStatus("error");
    }
  }

  return (
    <main className="p-8 max-w-md mx-auto space-y-4">
      <h1 className="text-xl font-semibold">Sign In</h1>
      <p>Enter your email to receive a secure magic sign-in link.</p>
      <form onSubmit={submit} className="space-y-3">
        <input
          type="email"
          required
          value={email}
            onChange={e=>setEmail(e.target.value)}
          placeholder="you@institution.edu"
          className="w-full border rounded px-3 py-2"
        />
        <button
          type="submit"
          disabled={status==="sending"}
          className="bg-gray-800 text-white px-4 py-2 rounded disabled:opacity-60"
        >
          {status==="sending" ? 'Sending…' : 'Send magic link'}
        </button>
      </form>
      {status === "sent" && <p className="text-green-600">Check your inbox for the link.</p>}
      {error && <p className="text-red-600">{error}</p>}
    </main>
  );
}
