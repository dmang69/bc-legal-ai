'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { auth, ApiError } from '../lib/api';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;
    auth
      .me()
      .then(() => {
        if (!cancelled) router.replace('/chat');
      })
      .catch((e) => {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 401) {
          router.replace('/login');
        } else {
          router.replace('/login');
        }
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-muted">Loading…</p>
    </div>
  );
}
