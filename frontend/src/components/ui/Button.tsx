import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'lg' | 'icon';
    loading?: boolean;
    icon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className = '', variant = 'primary', size = 'md', loading, icon, children, ...props }, ref) => {
        const baseStyles = "inline-flex items-center justify-center gap-2 font-bold transition-all active:scale-95 disabled:opacity-50 disabled:pointer-events-none rounded-2xl";

        const variants = {
            primary: "bg-black text-white hover:bg-zinc-900 border-2 border-transparent hover:border-zinc-700 shadow-lg shadow-black/5",
            secondary: "bg-zinc-100 text-zinc-900 hover:bg-zinc-200 border-2 border-transparent",
            ghost: "bg-transparent border-2 border-zinc-200 text-zinc-600 hover:border-black hover:text-black",
            danger: "bg-rose-500 text-white hover:bg-rose-600 shadow-lg shadow-rose-500/10"
        };

        const sizes = {
            sm: "px-4 py-2 text-xs",
            md: "px-6 py-3 text-sm",
            lg: "px-8 py-4 text-base",
            icon: "p-3"
        };

        return (
            <button
                ref={ref}
                className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
                disabled={loading || props.disabled}
                {...props}
            >
                {loading ? (
                    <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
                ) : icon}
                {children}
            </button>
        );
    }
);
