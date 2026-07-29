'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { auth, ApiError } from '../../lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [bootstrapToken, setBootstrapToken] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await auth.register({
        email,
        password,
        display_name: displayName,
        bootstrap_token: bootstrapToken || undefined,
      });
      router.push('/chat');
    } catch (err) {
      if (err instanceof ApiError) setError(err.detail);
      else setError('Registration failed');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-panel border border-border rounded-2xl p-8">
        <h1 className="text-2xl font-semibold mb-1">Create account</h1>
        <p className="text-muted text-sm mb-6">
          The first registered user becomes admin.
        </p>

        {error && (
          <div className="mb-4 text-sm bg-red-900/30 border border-red-800 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="text-sm text-muted mb-1 block">Display name</span>
            <input
              type="text"
              required
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full bg-card border border-border rounded-lg px-3 py-2 focus:outline-none focus:border-accent"
            />
          </label>
          <label className="block">
            <span className="text-sm text-muted mb-1 block">Email</span>
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-card border border-border rounded-lg px-3 py-2 focus:outline-none focus:border-accent"
            />
          </label>
          <label className="block">
            <span className="text-sm text-muted mb-1 block">Password (12+ characters)</span>
            <input
              type="password"
              required
              minLength={12}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-card border border-border rounded-lg px-3 py-2 focus:outline-none focus:border-accent"
            />
          </label>
          <label className="block">
            <span className="text-sm text-muted mb-1 block">
              Bootstrap token{' '}
              <span className="text-xs">(only if registration is closed)</span>
            </span>
            <input
              type="text"
              autoComplete="off"
              value={bootstrapToken}
              onChange={(e) => setBootstrapToken(e.target.value)}
              className="w-full bg-card border border-border rounded-lg px-3 py-2 focus:outline-none focus:border-accent"
            />
          </label>
          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-accent text-white rounded-lg px-4 py-2.5 disabled:opacity-50"
          >
            {submitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="text-sm text-muted mt-6 text-center">
          Already have an account?{' '}
          <Link href="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
