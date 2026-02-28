import Link from 'next/link';
import { Sparkles, CheckCircle, Zap, Shield, ArrowRight, FileText, Search, Clock } from 'lucide-react';
import type { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'GovPreneurs | Win Government Contracts with AI',
    description: 'Generate compliant federal proposals in minutes. AI-powered matching, drafting, and export for small businesses.',
};

export default function HomePage() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-govblue-900 via-govblue-800 to-govblue-700">
            {/* Hero */}
            <main className="px-8 pt-20 pb-24 max-w-5xl mx-auto text-center">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 border border-white/20 text-white/80 text-sm mb-8">
                    <Zap className="w-3.5 h-3.5 text-yellow-400" />
                    AI-Powered Government Proposal Generation
                </div>

                <h1 className="text-5xl md:text-6xl font-bold text-white leading-tight mb-6">
                    Win Government Contracts
                    <br />
                    <span className="text-yellow-400">10x Faster</span> with AI
                </h1>

                <p className="text-xl text-white/70 max-w-2xl mx-auto mb-10 leading-relaxed">
                    From SAM.gov opportunity to fully compliant federal proposal draft in under 10 minutes. Built for small businesses.
                </p>

                <div className="flex gap-4 justify-center flex-wrap">
                    <Link
                        href="/proposal-review"
                        className="flex items-center gap-2 px-8 py-4 bg-white text-govblue-700 rounded-2xl font-bold text-base hover:bg-govblue-50 transition-all shadow-2xl shadow-govblue-900/50 hover:-translate-y-0.5"
                    >
                        <Sparkles className="w-5 h-5" />
                        Generate a Proposal
                    </Link>
                    <a
                        href="http://localhost:8000/docs"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-8 py-4 bg-white/10 text-white border border-white/20 rounded-2xl font-bold text-base hover:bg-white/20 transition-all"
                    >
                        API Documentation
                    </a>
                </div>

                {/* Feature cards */}
                <div className="grid md:grid-cols-3 gap-5 mt-20">
                    {[
                        {
                            icon: Search,
                            title: 'SAM.gov Integration',
                            desc: 'Automatically ingest and track opportunities from SAM.gov with 6-hour refresh cycles.',
                        },
                        {
                            icon: Clock,
                            title: 'RAG-Powered Generation',
                            desc: 'Vector search matches your capabilities to solicitation requirements for precise, compliant proposals.',
                        },
                        {
                            icon: FileText,
                            title: 'Review & Export',
                            desc: 'Edit sections inline, refine with AI instructions, and export to PDF or Word in one click.',
                        },
                    ].map((f) => (
                        <div
                            key={f.title}
                            className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 text-left hover:bg-white/15 transition-all"
                        >
                            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center mb-4">
                                <f.icon className="w-5 h-5 text-white" />
                            </div>
                            <h3 className="text-white font-semibold mb-2">{f.title}</h3>
                            <p className="text-white/60 text-sm leading-relaxed">{f.desc}</p>
                        </div>
                    ))}
                </div>

                {/* Trust badges */}
                <div className="flex gap-6 justify-center mt-16 flex-wrap">
                    {[
                        'SAM.gov Verified',
                        'Federal Proposal Structure',
                        'Anti-Hallucination Guardrails',
                        'Export to PDF & Word',
                    ].map((badge) => (
                        <span
                            key={badge}
                            className="flex items-center gap-1.5 text-white/70 text-sm"
                        >
                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                            {badge}
                        </span>
                    ))}
                </div>
            </main>
        </div>
    );
}
