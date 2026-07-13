import React from 'react';

interface CardProps {
    children: React.ReactNode;
    className?: string;
    hover?: boolean;
}

export function Card({ children, className = '', hover = true }: CardProps) {
    return (
        <div className={`
            bg-white border border-zinc-100 rounded-[2rem] shadow-sm 
            ${hover ? 'hover:shadow-xl hover:shadow-zinc-200/40 transition-all duration-300' : ''} 
            ${className}
        `}>
            {children}
        </div>
    );
}

export function CardHeader({ title, subtitle, icon }: { title: string, subtitle?: string, icon?: React.ReactNode }) {
    return (
        <div className="flex items-center gap-4 mb-6">
            {icon && (
                <div className="w-12 h-12 rounded-2xl bg-zinc-50 flex items-center justify-center text-black">
                    {icon}
                </div>
            )}
            <div>
                <h3 className="text-xl font-bold text-zinc-900">{title}</h3>
                {subtitle && <p className="text-sm text-zinc-500 font-medium">{subtitle}</p>}
            </div>
        </div>
    );
}
