'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { auth } from '../lib/api';

export default function Home() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let cancelled = false;
    auth
      .me()
      .then(() => {
        if (!cancelled) router.replace('/chat');
      })
      .catch(() => {
        // not authenticated - show landing page
      })
      .finally(() => {
        if (!cancelled) setChecking(false);
      });
    return () => { cancelled = true; };
  }, [router]);

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted">Loading&hellip;</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 to-slate-900 text-white">
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-sm">AI</div>
          <span className="font-semibold text-lg">BC Legal AI Associate</span>
        </div>
        <div className="flex gap-3">
          <Link href="/login" className="px-4 py-2 rounded-lg border border-slate-700 hover:bg-slate-800 transition text-sm">
            Sign In
          </Link>
          <Link href="/register" className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 transition text-sm font-medium">
            Create Account
          </Link>
        </div>
      </header>

      <section className="max-w-4xl mx-auto px-6 py-16 md:py-24">
        <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-6">
          Welcome to Your AI Legal Assistant
        </h1>
        <p className="text-lg md:text-xl text-slate-300 leading-relaxed mb-8">
          Understand legal information, organize your matter, review documents, and prepare structured work product with greater clarity.
        </p>
        <p className="text-slate-400 mb-12">
          The AI Legal Assistant is a conversational legal-information and drafting-support platform designed to help users research legal issues, understand procedures, organize evidence, and prepare materials for independent review.
        </p>
        <div className="flex gap-4">
          <Link href="/register" className="px-6 py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 transition font-medium">
            Get Started
          </Link>
          <Link href="/login" className="px-6 py-3 rounded-lg border border-slate-700 hover:bg-slate-800 transition">
            Sign In
          </Link>
        </div>
      </section>

      <section className="max-w-4xl mx-auto px-6 py-12 border-t border-slate-800">
        <h2 className="text-2xl font-bold mb-8">How the AI Legal Assistant Can Help</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
            <h3 className="font-semibold text-lg mb-3">Legal Information</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Receive plain-language explanations of legal concepts, terminology, legislation, court procedures, and administrative processes.
            </p>
            <p className="text-slate-500 text-sm mt-3">
              The assistant identifies the jurisdiction and legal subject involved, highlights issues requiring verification, and distinguishes general information from conclusions that require professional legal judgment.
            </p>
          </div>
          <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
            <h3 className="font-semibold text-lg mb-3">Document Review</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Review contracts, letters, notices, decisions, pleadings, affidavits, transcripts, and other legal documents.
            </p>
            <ul className="text-slate-400 text-sm mt-3 space-y-1 list-disc list-inside">
              <li>Summarize important provisions</li>
              <li>Identify deadlines, obligations, and disputed language</li>
              <li>Flag inconsistencies or missing information</li>
              <li>Separate facts, allegations, assumptions, and legal arguments</li>
              <li>Identify provisions that may require independent legal review</li>
            </ul>
          </div>
          <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
            <h3 className="font-semibold text-lg mb-3">Drafting Support</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Prepare structured drafts of correspondence, procedural documents, chronologies, issue summaries, research memoranda, argument outlines, and other legal work product.
            </p>
            <p className="text-slate-500 text-sm mt-3">
              Drafts are prepared for review, correction, and approval before they are sent, relied upon, or filed.
            </p>
          </div>
          <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
            <h3 className="font-semibold text-lg mb-3">Rights and Responsibilities</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Explore the legal rules that may affect situations involving housing and tenancy, contracts, employment, consumer matters, family disputes, civil litigation, administrative decisions, real estate, intellectual property, and regulatory and procedural issues.
            </p>
          </div>
          <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
            <h3 className="font-semibold text-lg mb-3">Legal Research Support</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Organize legal research using legislation, regulations, court rules, reported decisions, tribunal materials, and other authoritative sources.
            </p>
            <ul className="text-slate-400 text-sm mt-3 space-y-1 list-disc list-inside">
              <li>Identify potentially relevant authorities</li>
              <li>Explain the legal principle associated with an authority</li>
              <li>Distinguish binding from persuasive sources</li>
              <li>Identify adverse or competing authority</li>
              <li>Flag citations and quotations requiring verification</li>
              <li>Connect legal propositions to the facts and evidence in the record</li>
            </ul>
          </div>
          <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
            <h3 className="font-semibold text-lg mb-3">Procedural Guidance</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Break complex legal processes into manageable steps, including identifying the proper court or tribunal, determining required forms, organizing service and filing information, preparing procedural checklists, identifying potential deadlines, and tracking evidence and outstanding tasks.
            </p>
          </div>
      </section>

      <section className="max-w-4xl mx-auto px-6 py-12 border-t border-slate-800">
        <h2 className="text-2xl font-bold mb-6">Important Limitations</h2>
        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
          <p className="text-slate-300 mb-4">
            The AI Legal Assistant provides legal information, organizational assistance, research support, and drafting support.
          </p>
          <ul className="text-slate-400 text-sm space-y-2">
            <li className="flex gap-2"><span className="text-red-400 shrink-0">&times;</span> Is not a lawyer</li>
            <li className="flex gap-2"><span className="text-red-400 shrink-0">&times;</span> Does not provide formal legal advice</li>
            <li className="flex gap-2"><span className="text-red-400 shrink-0">&times;</span> Does not represent users before a court or tribunal</li>
            <li className="flex gap-2"><span className="text-red-400 shrink-0">&times;</span> Does not establish a lawyer-client or solicitor-client relationship</li>
            <li className="flex gap-2"><span className="text-red-400 shrink-0">&times;</span> Cannot guarantee that legal information is complete, current, or applicable to every situation</li>
            <li className="flex gap-2"><span className="text-red-400 shrink-0">&times;</span> Cannot replace independent professional judgment</li>
            <li className="flex gap-2"><span className="text-red-400 shrink-0">&times;</span> Does not automatically file documents, accept settlements, waive privilege, or make binding legal decisions</li>
          </ul>
          <p className="text-slate-500 text-sm mt-4">
            Documents and analysis generated by the platform should be reviewed by a qualified lawyer before they are relied upon, served, signed, submitted, or filed.
          </p>
        </div>
      </section>

      <section className="max-w-4xl mx-auto px-6 py-12 border-t border-slate-800">
        <h2 className="text-2xl font-bold mb-6">Privacy Notice</h2>
        <div className="bg-amber-950/40 rounded-xl p-6 border border-amber-900/50">
          <p className="text-amber-200 text-sm leading-relaxed">
            <strong>Do not submit confidential, privileged, identifying, or active-matter information to a public demonstration.</strong>
          </p>
          <p className="text-amber-300/70 text-sm mt-3">
            Confidential legal records should only be processed in an approved private environment with appropriate authentication, access controls, encryption, retention rules, audit logging, and organizational authorization.
          </p>
        </div>
      </section>

      <footer className="border-t border-slate-800 px-6 py-8 text-center text-sm text-slate-500">
        <p>BC Legal AI Associate &mdash; Not a lawyer. Not legal advice. Human supervision required.</p>
      </footer>
    </div>
  );
}
