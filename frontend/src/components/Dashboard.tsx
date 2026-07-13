import { AnalysisResult } from '../types';
import {
    Radar, RadarChart, PolarGrid, PolarAngleAxis, Tooltip, ResponsiveContainer
} from 'recharts';
import {
    CheckCircle, XCircle, Download, RefreshCw,
    Activity, Star, Shield, Info, ArrowUpRight
} from 'lucide-react';
import { Button } from './ui/Button.tsx';
import { Card } from './ui/Card.tsx';

interface DashboardProps {
    results: AnalysisResult;
    onReset: () => void;
    onDownloadPdf: () => void;
}

export default function Dashboard({ results, onReset, onDownloadPdf }: DashboardProps) {
    const { found_skills, missing_skills, explanation } = results;

    const radarData = [
        { subject: 'Role Fit', A: results.role_fit, fullMark: 100 },
        { subject: 'ML Score', A: results.ml_score, fullMark: 100 },
        { subject: 'Skills', A: results.skill_similarity, fullMark: 100 },
        { subject: 'ATS Score', A: results.ats_score, fullMark: 100 },
        { subject: 'Semantic', A: results.semantic_score, fullMark: 100 },
    ];

    return (
        <div className="space-y-10 py-6 animate-in fade-in zoom-in-95 duration-700">
            {/* Result Header */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 bg-black p-10 rounded-[2.5rem] text-white shadow-2xl">
                <div className="space-y-3">
                    <div className="flex items-center gap-2 text-zinc-400 font-black text-[10px] tracking-widest uppercase">
                        <Activity size={12} /> Analysis Summary
                    </div>
                    <h1 className="text-4xl font-black">{results.role} Assessment</h1>
                    <p className="text-zinc-500 font-medium max-w-lg leading-relaxed">Verified by AI Talent Scout Pro Intelligence Engine. Cross-referenced against 2024 industry standards.</p>
                </div>
                <div className="flex flex-wrap gap-4">
                    <Button
                        onClick={onDownloadPdf}
                        variant="primary"
                        icon={<Download size={18} />}
                        className="bg-white text-black hover:bg-zinc-100"
                    >
                        Export PDF
                    </Button>
                    <Button
                        onClick={onReset}
                        variant="ghost"
                        icon={<RefreshCw size={18} />}
                        className="border-white/20 text-white hover:border-white hover:bg-white/10"
                    >
                        New Analysis
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Main Recommendation Card */}
                <div className="lg:col-span-8 space-y-8">
                    <Card className="overflow-hidden border-none" hover={false}>
                        <div className="bg-black p-12 text-center relative overflow-hidden">
                            {/* Background glow */}
                            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.08),transparent_70%)]" />
                            <p className="text-[10px] font-black tracking-[0.3em] text-zinc-500 uppercase mb-4 relative z-10">Neural Compatibility Match</p>
                            <div className="text-8xl font-black text-white mb-8 relative z-10 flex items-center justify-center gap-4">
                                {Math.round(results.role_fit)}<span className="text-zinc-500 text-4xl">%</span>
                            </div>
                            <div className={`
                                inline-flex items-center gap-3 px-8 py-4 rounded-full font-black text-sm relative z-10 tracking-widest uppercase
                                ${results.role_fit > 80 ? 'bg-white text-black' : 'bg-amber-500 text-white'}
                            `}>
                                <Shield size={18} /> {results.decision}
                            </div>
                        </div>

                        <div className="p-10 grid grid-cols-2 md:grid-cols-4 gap-10 bg-white">
                            <MiniStat label="ATS Score" value={results.ats_score} unit="/100" />
                            <MiniStat label="ML Proficiency" value={results.ml_score} unit="/100" />
                            <MiniStat label="Semantic Similarity" value={Math.round(results.semantic_score)} unit="%" />
                            <MiniStat label="Experience" value={results.experience} unit=" yrs" />
                        </div>
                    </Card>

                    <Card className="p-10">
                        <h3 className="text-xl font-black text-zinc-900 mb-8 flex items-center gap-3">
                            <Info className="text-black" /> AI Explainability Benchmarks
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                            <div className="space-y-6">
                                <h4 className="text-[10px] font-black text-emerald-600 uppercase tracking-widest flex items-center gap-2">
                                    <CheckCircle size={14} /> Key Strengths
                                </h4>
                                <ul className="space-y-4">
                                    {explanation.selected_reasons.map((r, i) => (
                                        <li key={i} className="flex gap-3 text-sm font-bold text-zinc-600 leading-relaxed group">
                                            <div className="w-1.5 h-1.5 rounded-full bg-black mt-2 shrink-0 group-hover:scale-150 transition-transform" />
                                            {r}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            <div className="space-y-6">
                                <h4 className="text-[10px] font-black text-rose-500 uppercase tracking-widest flex items-center gap-2">
                                    <XCircle size={14} /> Strategy Gaps
                                </h4>
                                <ul className="space-y-4">
                                    {explanation.rejected_reasons.map((r, i) => (
                                        <li key={i} className="flex gap-3 text-sm font-bold text-zinc-600 leading-relaxed">
                                            <div className="w-1.5 h-1.5 rounded-full bg-rose-500 mt-2 shrink-0" />
                                            {r}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </Card>
                </div>

                {/* Visual Analytics Column */}
                <div className="lg:col-span-4 space-y-8 h-full">
                    <Card className="p-8 h-fit">
                        <h3 className="text-[10px] font-black text-zinc-400 mb-6 text-center uppercase tracking-widest">Score Architecture</h3>
                        <div className="h-64 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                                    <PolarGrid stroke="#f4f4f5" />
                                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#a1a1aa', fontSize: 10, fontWeight: 900 }} />
                                    <Radar
                                        name="Score"
                                        dataKey="A"
                                        stroke="#000000"
                                        fill="#000000"
                                        fillOpacity={0.1}
                                    />
                                    <Tooltip contentStyle={{ borderRadius: '16px', border: 'none', fontWeight: 'bold' }} />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </Card>

                    <Card className="p-8 bg-zinc-50 border-none shadow-none" hover={false}>
                        <h3 className="text-[10px] font-black text-black mb-6 flex items-center gap-2 uppercase tracking-widest">
                            <ArrowUpRight className="text-black" size={16} /> Market Recommendations
                        </h3>
                        <div className="space-y-3">
                            {results.top_roles.map((r, i) => (
                                <div key={i} className="bg-white p-4 rounded-xl flex items-center justify-between shadow-sm border border-zinc-100 hover:border-black transition-all cursor-default group">
                                    <div className="flex items-center gap-3">
                                        <span className="text-[10px] font-black text-zinc-300 group-hover:text-black transition-colors">0{i + 1}</span>
                                        <span className="text-sm font-bold text-zinc-600 group-hover:text-black transition-colors">{r[0]}</span>
                                    </div>
                                    <span className="text-sm font-black text-black">{Math.round(r[1])}%</span>
                                </div>
                            ))}
                        </div>
                    </Card>

                    <div className="bg-zinc-900 p-8 rounded-[2rem] text-white shadow-xl italic relative overflow-hidden group">
                        <Star className="absolute -top-4 -right-4 text-white/10 w-24 h-24 rotate-12 group-hover:scale-125 transition-transform duration-700" />
                        <p className="text-sm font-bold relative z-10 leading-relaxed text-zinc-300">
                            "Our neural cross-analysis suggests you are a high-value match for <span className="text-white underline decoration-white/20 underline-offset-4">{results.top_roles[0]?.[0]}</span>. Focus on highlighting your {found_skills.slice(0, 2).join(' and ')} proficiency during interviews."
                        </p>
                    </div>
                </div>
            </div>

            {/* Skill Matrix */}
            {/* Skill Matrix */}
            <Card className="p-10">
                <div className="flex items-center justify-between mb-12">
                    <div>
                        <h3 className="text-2xl font-black text-zinc-900">Skill Alignment Matrix</h3>
                        <p className="text-zinc-500 font-medium">Mapped against <span className="text-black font-bold">{results.role}</span> requirements</p>
                    </div>
                    <div className="text-right">
                        <div className="text-4xl font-black text-black tracking-tight">{found_skills.length} / {found_skills.length + missing_skills.length}</div>
                        <p className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">Matched Assets</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                    <div className="space-y-6">
                        <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">Technological Strengths</h4>
                        <div className="flex flex-wrap gap-2">
                            {found_skills.map((s, i) => (
                                <span key={i} className="px-5 py-2.5 rounded-xl bg-zinc-900 text-white font-bold text-xs shadow-lg shadow-black/5 hover:scale-105 transition-transform cursor-default">
                                    {s}
                                </span>
                            ))}
                        </div>
                    </div>
                    <div className="space-y-6">
                        <h4 className="text-[10px] font-black text-zinc-400 uppercase tracking-widest text-right">Learning Opportunities</h4>
                        <div className="flex flex-wrap gap-2 justify-end">
                            {missing_skills.map((s, i) => (
                                <span key={i} className="px-5 py-2.5 rounded-xl bg-zinc-50 text-zinc-500 font-bold text-xs border border-zinc-100 hover:border-black hover:text-black transition-all cursor-default">
                                    {s}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>
            </Card>
        </div>
    );
}

function MiniStat({ label, value, unit }: any) {
    return (
        <div className="text-center space-y-1">
            <p className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">{label}</p>
            <div className="text-xl font-black text-zinc-900">
                {typeof value === 'number' && !label.includes('Experience') ? Math.round(value) : value}
                {unit && <span className="text-zinc-400 text-sm ml-0.5">{unit}</span>}
            </div>
        </div>
    );
}
