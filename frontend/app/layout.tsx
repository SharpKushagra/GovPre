import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '../styles/globals.css';
import { Providers } from './providers';
import { Navbar } from '@/components/Navbar';

const inter = Inter({
    subsets: ['latin'],
    variable: '--font-inter',
    display: 'swap',
});

export const metadata: Metadata = {
    title: {
        default: 'GovPreneurs | Auto-Proposal Generator',
        template: '%s | GovPreneurs',
    },
    description:
        'AI-powered government contract proposal generation for small businesses. Go from opportunity to compliant draft in under 10 minutes.',
    keywords: ['government contracts', 'SAM.gov', 'proposal writing', 'federal contracts', 'small business'],
    openGraph: {
        title: 'GovPreneurs Auto-Proposal',
        description: 'Win more government contracts with AI-powered proposal generation',
        type: 'website',
    },
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body className={`${inter.variable} font-sans antialiased`}>
                <Providers>
                    <Navbar />
                    <div className="pt-14">{children}</div>
                </Providers>
            </body>
        </html>
    );
}
