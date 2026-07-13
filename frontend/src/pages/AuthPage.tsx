import React, { useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../services/api';
import { Mail, Lock, User, ShieldCheck, ArrowRight, Loader2 } from 'lucide-react';

export default function AuthPage() {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [role, setRole] = useState<'candidate' | 'recruiter'>('candidate');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const setAuth = useAuthStore((state) => state.setAuth);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            if (isLogin) {
                const data = await authApi.login(email, password);
                const user = await authApi.me(); // This might need the token set first if not handled by interceptor
                setAuth(user, data.access_token);
            } else {
                await authApi.register({ email, password, full_name: fullName, role });
                // After register, auto-login
                const data = await authApi.login(email, password);
                const user = await authApi.me();
                setAuth(user, data.access_token);
            }
        } catch (err: any) {
            setError(err.response?.data?.error || 'Authentication failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-black flex items-center justify-center p-4">
            {/* Background blobs */}
            <div className="absolute top-1/4 -left-20 w-80 h-80 bg-zinc-800/20 rounded-full blur-[100px] pointer-events-none" />
            <div className="absolute bottom-1/4 -right-20 w-80 h-80 bg-zinc-800/10 rounded-full blur-[100px] pointer-events-none" />

            <div className="w-full max-w-md relative">
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl overflow-hidden">
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white p-0.5 mb-6">
                            <div className="w-full h-full bg-black rounded-[14px] flex items-center justify-center">
                                <ShieldCheck className="text-white" size={32} />
                            </div>
                        </div>
                        <h1 className="text-3xl font-bold text-white mb-2">
                            {isLogin ? 'Welcome Back' : 'Create Account'}
                        </h1>
                        <p className="text-zinc-500">
                            {isLogin ? 'Sign in to access your dashboard' : 'Join AI Talent Scout Pro today'}
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {!isLogin && (
                            <>
                                <div className="relative group">
                                    <User className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 group-focus-within:text-white transition-colors" size={20} />
                                    <input
                                        type="text"
                                        required
                                        placeholder="Full Name"
                                        value={fullName}
                                        onChange={(e) => setFullName(e.target.value)}
                                        className="w-full bg-zinc-900/50 border border-zinc-800 text-white pl-12 pr-4 py-4 rounded-xl outline-none focus:border-white/50 focus:ring-4 focus:ring-white/10 transition-all placeholder:text-zinc-600"
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-3 p-1 bg-zinc-900/50 border border-zinc-800 rounded-xl">
                                    <button
                                        type="button"
                                        onClick={() => setRole('candidate')}
                                        className={`py-2 text-sm font-bold rounded-lg transition-all ${role === 'candidate' ? 'bg-white text-black shadow-lg' : 'text-zinc-500 hover:text-white'}`}
                                    >
                                        Candidate
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setRole('recruiter')}
                                        className={`py-2 text-sm font-bold rounded-lg transition-all ${role === 'recruiter' ? 'bg-white text-black shadow-lg' : 'text-zinc-500 hover:text-white'}`}
                                    >
                                        Recruiter
                                    </button>
                                </div>
                            </>
                        )}

                        <div className="relative group">
                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 group-focus-within:text-white transition-colors" size={20} />
                            <input
                                type="email"
                                required
                                placeholder="Email Address"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full bg-zinc-900/50 border border-zinc-800 text-white pl-12 pr-4 py-4 rounded-xl outline-none focus:border-white/50 focus:ring-4 focus:ring-white/10 transition-all placeholder:text-zinc-600"
                            />
                        </div>

                        <div className="relative group">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 group-focus-within:text-white transition-colors" size={20} />
                            <input
                                type="password"
                                required
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-zinc-900/50 border border-zinc-800 text-white pl-12 pr-4 py-4 rounded-xl outline-none focus:border-white/50 focus:ring-4 focus:ring-white/10 transition-all placeholder:text-zinc-600"
                            />
                        </div>

                        {error && (
                            <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl text-sm font-medium">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-white text-black font-bold py-4 rounded-xl shadow-lg shadow-white/5 hover:shadow-white/20 hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2 group disabled:opacity-50 disabled:hover:translate-y-0"
                        >
                            {loading ? (
                                <Loader2 className="animate-spin" size={22} />
                            ) : (
                                <>
                                    {isLogin ? 'Sign In' : 'Get Started'}
                                    <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-8 text-center">
                        <button
                            onClick={() => setIsLogin(!isLogin)}
                            className="text-zinc-500 hover:text-white text-sm font-medium transition-colors"
                        >
                            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
