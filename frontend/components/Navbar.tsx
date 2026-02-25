'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Sparkles, Building2, FileText, Settings, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

const NAV_LINKS = [
    { href: '/opportunities', label: 'Opportunities', icon: Building2 },
    { href: '/proposal-review', label: 'Proposal Editor', icon: FileText },
];

export function Navbar() {
    const pathname = usePathname();
    const [mobileOpen, setMobileOpen] = useState(false);

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border bg-card/90 backdrop-blur-md">
            <div className="max-w-7xl mx-auto px-4 sm:px-6">
                <div className="flex items-center justify-between h-14">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2.5 group">
                        <div className="w-8 h-8 rounded-lg bg-govblue-600 flex items-center justify-center shadow-sm group-hover:bg-govblue-700 transition-colors">
                            <Sparkles className="w-4 h-4 text-white" />
                        </div>
                        <div className="hidden sm:block">
                            <span className="font-bold text-sm text-foreground leading-none block">GovPreneurs</span>
                            <span className="text-[10px] text-muted-foreground leading-none">Auto-Proposal</span>
                        </div>
                    </Link>

                    {/* Desktop nav */}
                    <div className="hidden md:flex items-center gap-1">
                        {NAV_LINKS.map(({ href, label, icon: Icon }) => {
                            const active = pathname.startsWith(href);
                            return (
                                <Link
                                    key={href}
                                    href={href}
                                    className={cn(
                                        'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                                        active
                                            ? 'bg-govblue-600 text-white shadow-sm'
                                            : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                                    )}
                                >
                                    <Icon className="w-3.5 h-3.5" />
                                    {label}
                                </Link>
                            );
                        })}
                    </div>

                    {/* Right controls */}
                    <div className="flex items-center gap-2">
                        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="text-xs text-emerald-700 font-medium">API Ready</span>
                        </div>

                        {/* Mobile hamburger */}
                        <button
                            className="md:hidden p-1.5 rounded-lg hover:bg-muted transition"
                            onClick={() => setMobileOpen(!mobileOpen)}
                        >
                            {mobileOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
                        </button>
                    </div>
                </div>

                {/* Mobile menu */}
                {mobileOpen && (
                    <div className="md:hidden border-t border-border py-2 space-y-1 animate-fade-in">
                        {NAV_LINKS.map(({ href, label, icon: Icon }) => {
                            const active = pathname.startsWith(href);
                            return (
                                <Link
                                    key={href}
                                    href={href}
                                    onClick={() => setMobileOpen(false)}
                                    className={cn(
                                        'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all',
                                        active
                                            ? 'bg-govblue-600 text-white'
                                            : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                                    )}
                                >
                                    <Icon className="w-4 h-4" />
                                    {label}
                                </Link>
                            );
                        })}
                    </div>
                )}
            </div>
        </nav>
    );
}
