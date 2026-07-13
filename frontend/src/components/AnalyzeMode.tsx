import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { resumeApi } from '../services/api';
import { RoleInfo, AnalysisResult } from '../types';
import {
    Upload, FileText, Brain,
    Activity, Loader2, Sparkles, ChevronRight, Zap
} from 'lucide-react';
import { Button } from './ui/Button.tsx';
import { Card, CardHeader } from './ui/Card.tsx';

interface AnalyzeModeProps {
    roles: RoleInfo[];
    onResult: (res: AnalysisResult) => void;
}

export default function AnalyzeMode({ roles, onResult }: AnalyzeModeProps) {
    const [file, setFile] = useState<File | null>(null);
    const [targetRole, setTargetRole] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            setFile(acceptedFiles[0]);
            setError(null);
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'text/plain': ['.txt'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
        },
        multiple: false
    });

    const handleAnalyze = async () => {
        if (!file) return;
        setLoading(true);
        setError(null);
        try {
            const roleToUse = targetRole || (roles.length > 0 ? roles[0].name : '');
            const res = await resumeApi.analyze(file, roleToUse);
            onResult(res);
        } catch (err: any) {
            setError(err.response?.data?.error || "Analysis failed. Please check your file.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-5xl mx-auto space-y-10 py-4 animate-in slide-in-from-bottom-5 duration-500">
            <div className="text-center space-y-4">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-black text-white text-xs font-black tracking-widest uppercase">
                    <Sparkles size={14} /> New Semantic V2 Engine
                </div>
                <h1 className="text-5xl font-black text-black tracking-tight">
                    Precision <span className="text-zinc-500">Talent Scouting</span>
                </h1>
                <p className="text-lg text-zinc-500 max-w-2xl mx-auto font-medium">
                    Upload your resume and let our neural networks cross-match your expertise against industry standards using semantic embeddings. No keywords required.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                {/* Left Column: Upload */}
                <div className="lg:col-span-7 space-y-6">
                    <Card className="p-8">
                        <CardHeader
                            title="Source Document"
                            subtitle="Upload candidate resume"
                            icon={<Upload size={22} />}
                        />

                        <div
                            {...getRootProps()}
                            className={`
                                group relative border-2 border-dashed rounded-[2rem] p-12 text-center cursor-pointer transition-all duration-300
                                ${isDragActive ? 'border-black bg-zinc-50' : 'border-zinc-200 hover:border-black hover:bg-zinc-50'}
                            `}
                        >
                            <input {...getInputProps()} />
                            <div className="flex flex-col items-center">
                                <div className={`
                                  mb-6 w-20 h-20 rounded-3xl flex items-center justify-center transition-all duration-300
                                  ${file ? 'bg-black text-white px-2' : 'bg-zinc-50 text-zinc-400 group-hover:bg-black group-hover:text-white'}
                                `}>
                                    <FileText size={40} />
                                </div>
                                {file ? (
                                    <div className="space-y-1">
                                        <p className="text-lg font-bold text-zinc-900">{file.name}</p>
                                        <p className="text-sm text-zinc-400 font-medium">{(file.size / 1024).toFixed(1)} KB • Ready for analysis</p>
                                    </div>
                                ) : (
                                    <>
                                        <p className="text-lg font-bold text-zinc-700 mb-1 font-sans">Drop your resume here</p>
                                        <p className="text-sm text-zinc-400 font-medium">Supports PDF, Word, or Plain Text</p>
                                    </>
                                )}
                            </div>
                        </div>
                    </Card>

                    {error && (
                        <div className="bg-rose-50 border border-rose-100 p-4 rounded-2xl flex items-center gap-3 text-rose-600 text-sm font-bold animate-in slide-in-from-top-2">
                            <Activity size={18} /> {error}
                        </div>
                    )}
                </div>

                {/* Right Column: Settings & CTA */}
                <div className="lg:col-span-5 space-y-6 h-full">
                    <div className="bg-black p-8 rounded-[2rem] text-white shadow-2xl shadow-zinc-900/20 relative overflow-hidden group h-full">
                        {/* Glossy overlay */}
                        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-[80px] pointer-events-none group-hover:bg-white/10 transition-all duration-500" />

                        <div className="relative z-10 flex flex-col h-full">
                            <div className="flex items-center gap-3 mb-8">
                                <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center text-white">
                                    <Zap size={22} />
                                </div>
                                <h2 className="text-xl font-bold">Target Position</h2>
                            </div>

                            <div className="space-y-6 flex-1">
                                <div className="space-y-2">
                                    <label className="text-xs font-black tracking-widest text-zinc-500 uppercase">Selected Role</label>
                                    <select
                                        value={targetRole}
                                        onChange={e => setTargetRole(e.target.value)}
                                        className="w-full bg-white/5 border border-white/10 p-4 rounded-2xl text-white font-bold outline-none focus:border-white/40 transition-colors appearance-none"
                                    >
                                        {roles.map(r => <option key={r.name} value={r.name} className="bg-black text-white">{r.name}</option>)}
                                    </select>
                                </div>

                                <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                                    <p className="text-xs font-medium text-zinc-400 leading-relaxed italic">
                                        "AI Talent Scout will prioritize {targetRole || (roles[0]?.name)} specific skills and experience weights for this assessment."
                                    </p>
                                </div>
                            </div>

                            <Button
                                onClick={handleAnalyze}
                                disabled={loading || !file}
                                loading={loading}
                                size="lg"
                                className="w-full mt-10"
                                variant="primary"
                                style={{ backgroundColor: 'white', color: 'black' }}
                            >
                                <span>Start Analysis</span>
                                {!loading && <ChevronRight size={20} />}
                            </Button>
                        </div>
                    </div>

                    <Card className="p-6 rounded-[2rem] flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-zinc-50 flex items-center justify-center text-black">
                            <Brain size={24} />
                        </div>
                        <div>
                            <p className="text-sm font-bold text-zinc-900">Neural Engine v2.4</p>
                            <p className="text-xs text-zinc-500 font-medium">Equipped with 384-dim semantic vectors.</p>
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
}
