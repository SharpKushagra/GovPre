import * as React from 'react';
import { cn } from '@/lib/utils';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    variant?: 'default' | 'secondary' | 'success' | 'warning' | 'destructive' | 'outline';
}

const variantClasses: Record<string, string> = {
    default: 'bg-primary/10 text-primary border-primary/20',
    secondary: 'bg-secondary text-secondary-foreground border-border',
    success: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    warning: 'bg-amber-50 text-amber-700 border-amber-200',
    destructive: 'bg-red-50 text-red-700 border-red-200',
    outline: 'bg-transparent border-border text-foreground',
};

export function Badge({ className, variant = 'default', children, ...props }: BadgeProps) {
    return (
        <span
            className={cn(
                'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border',
                variantClasses[variant],
                className,
            )}
            {...props}
        >
            {children}
        </span>
    );
}
