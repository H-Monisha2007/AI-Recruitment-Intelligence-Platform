import { useEffect, useState } from 'react';
import { analyticsApi } from '../services/api';
import { DashboardStats } from '../types';
import {
    PieChart, Pie, Cell, ResponsiveContainer, Tooltip
} from 'recharts';
import {
    Users, FileText, CheckCircle, Activity,
    Clock, UserCheck
} from 'lucide-react';
import { Card } from '../components/ui/Card.tsx';

const COLORS = ['#10b981', '#f59e0b', '#ec4899', '#ef4444'];

export default function RecruiterDashboard() {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        analyticsApi.dashboard()
            .then(setStats)
            .finally(() => setLoading(false));
    }, []);

    if (loading) return (
        <div className="flex items-center justify-center h-full">
            <div className="animate-pulse text-zinc-400 font-bold text-xl">Loading Analytics...</div>
        </div>
    );

    if (!stats) return <div>Failed to load stats.</div>;

    const pieData = Object.entries(stats.decisions_breakdown).map(([name, value]) => ({ name, value }));

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-bold text-zinc-900">Recruiter Insights</h1>
                <p className="text-zinc-500">Real-time overview of candidates and hiring performance.</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    icon={<Users className="text-zinc-900" />}
                    label="Total Candidates"
                    value={stats.total_users}
                    trend="+12%"
                />
                <StatCard
                    icon={<FileText className="text-zinc-900" />}
                    label="Resumes Scanned"
                    value={stats.total_resumes_analyzed}
                    trend="+5.4%"
                />
                <StatCard
                    icon={<UserCheck className="text-zinc-900" />}
                    label="Avg Role Fit"
                    value={`${stats.avg_role_fit}%`}
                    trend="+2.1%"
                />
                <StatCard
                    icon={<Activity className="text-zinc-900" />}
                    label="ATS Compliance"
                    value={`${stats.avg_ats_score}%`}
                    trend="-0.5%"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Decision Breakdown */}
                <Card className="lg:col-span-1 p-8">
                    <h3 className="text-xl font-black mb-8 flex items-center gap-3">
                        <CheckCircle className="text-black" size={24} /> Decision Distribution
                    </h3>
                    <div className="h-[250px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={pieData}
                                    innerRadius={70}
                                    outerRadius={90}
                                    paddingAngle={8}
                                    dataKey="value"
                                >
                                    {pieData.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)', fontWeight: 'bold' }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="mt-8 space-y-3">
                        {pieData.map((d, i) => (
                            <div key={i} className="flex items-center justify-between text-sm group">
                                <div className="flex items-center gap-3">
                                    <div className="w-2.5 h-2.5 rounded-full ring-4 ring-zinc-50" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                                    <span className="text-zinc-500 font-bold group-hover:text-black transition-colors">{d.name}</span>
                                </div>
                                <span className="font-black text-zinc-900 bg-zinc-50 px-2 py-1 rounded-lg">{d.value}</span>
                            </div>
                        ))}
                    </div>
                </Card>

                {/* Recent Analyses Table */}
                <Card className="lg:col-span-2 p-8 overflow-hidden" hover={false}>
                    <h3 className="text-xl font-black mb-8 flex items-center gap-3">
                        <Clock className="text-black" size={24} /> Talent Assessment Stream
                    </h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="text-zinc-400 text-[10px] font-black uppercase tracking-widest border-b border-zinc-100">
                                    <th className="pb-5">Candidate</th>
                                    <th className="pb-5 text-center">Score</th>
                                    <th className="pb-5 text-center">ATS</th>
                                    <th className="pb-5">Decision</th>
                                    <th className="pb-5 text-right">Timestamp</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-50">
                                {stats.recent_analyses.map((item, i) => (
                                    <tr key={i} className="group hover:bg-zinc-50/50 transition-colors">
                                        <td className="py-5">
                                            <div className="font-bold text-zinc-900 group-hover:text-black transition-colors">{item.candidate}</div>
                                            <div className="text-[10px] text-zinc-400 font-medium group-hover:text-zinc-500 transition-colors uppercase tracking-tight">{item.email}</div>
                                        </td>
                                        <td className="py-5 text-center">
                                            <span className={`text-sm font-black ${item.role_fit > 70 ? 'text-emerald-500' : 'text-amber-500'}`}>
                                                {item.role_fit}%
                                            </span>
                                        </td>
                                        <td className="py-5 text-center text-sm font-black text-zinc-900">{item.ats_score}%</td>
                                        <td className="py-5 text-sm font-bold">
                                            <span className={`px-4 py-1.5 rounded-full text-[9px] font-black uppercase tracking-widest ${item.decision.includes('HIRE') ? 'bg-zinc-900 text-white shadow-lg shadow-black/10' :
                                                    item.decision.includes('INTERVIEW') ? 'bg-zinc-100 text-black' : 'bg-white border border-zinc-200 text-zinc-400'
                                                }`}>
                                                {item.decision}
                                            </span>
                                        </td>
                                        <td className="py-5 text-right text-[10px] text-zinc-400 font-bold uppercase tracking-tighter">
                                            {new Date(item.created_at).toLocaleDateString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Card>
            </div>
        </div>
    );
}

function StatCard({ icon, label, value, trend }: any) {
    return (
        <Card className="p-8">
            <div className="w-14 h-14 rounded-2xl bg-zinc-50 flex items-center justify-center mb-6 text-2xl group-hover:scale-110 transition-transform">
                {icon}
            </div>
            <div className="text-[10px] font-black text-zinc-400 mb-2 uppercase tracking-widest">{label}</div>
            <div className="flex items-end justify-between">
                <div className="text-3xl font-black text-zinc-950 tracking-tight">{value}</div>
                <div className={`text-[10px] font-black px-3 py-1.5 rounded-xl uppercase tracking-widest ${trend.startsWith('+') ? 'text-emerald-600 bg-emerald-50' : 'text-rose-600 bg-rose-50'}`}>
                    {trend}
                </div>
            </div>
        </Card>
    );
}
