import { Brain, CheckCircle2, XCircle, Sparkles } from 'lucide-react';
import { ExplanationData } from '../types';

interface ExplainableAIProps {
    explanation: ExplanationData;
    decision: string;
    confidence: number;
}

export default function ExplainableAI({ explanation, decision, confidence }: ExplainableAIProps) {
    const getDecisionColor = (dec: string) => {
        switch (dec.toUpperCase()) {
            case 'HIRE': return 'text-emerald-500 bg-emerald-50 border-emerald-200';
            case 'REVIEW': return 'text-amber-500 bg-amber-50 border-amber-200';
            case 'REJECT': return 'text-rose-500 bg-rose-50 border-rose-200';
            default: return 'text-zinc-500 bg-zinc-50 border-zinc-200';
        }
    };

    const decisionStyle = getDecisionColor(decision);

    return (
        <div className="bg-white rounded-3xl border border-zinc-100 p-6 shadow-sm overflow-hidden relative">
            <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                <Brain size={120} />
            </div>

            <div className="flex items-center gap-3 mb-6 relative z-10">
                <div className="w-12 h-12 bg-indigo-50 rounded-2xl flex items-center justify-center border border-indigo-100">
                    <Sparkles className="text-indigo-500" size={24} />
                </div>
                <div>
                    <h3 className="text-xl font-bold text-zinc-800">Explainable AI (XAI)</h3>
                    <p className="text-xs text-zinc-500 font-medium">Transparent reasoning behind the AI's recommendation</p>
                </div>
            </div>

            <div className={`p-4 rounded-2xl border ${decisionStyle} mb-6 flex items-center justify-between`}>
                <div>
                    <p className="text-xs font-black uppercase tracking-widest opacity-60 mb-1">AI Recommendation</p>
                    <p className="text-2xl font-bold">{decision.toUpperCase()}</p>
                </div>
                <div className="text-right">
                    <p className="text-xs font-black uppercase tracking-widest opacity-60 mb-1">Confidence</p>
                    <p className="text-2xl font-bold">{confidence}%</p>
                </div>
            </div>

            <div className="space-y-6 relative z-10">
                {/* Reasoning Text */}
                {explanation.ai_reasoning && (
                    <div className="bg-zinc-50 p-4 rounded-2xl border border-zinc-100">
                        <h4 className="flex items-center gap-2 text-sm font-bold text-zinc-700 mb-2">
                            <Brain size={16} className="text-indigo-500" />
                            AI Reasoning
                        </h4>
                        <p className="text-sm text-zinc-600 leading-relaxed">
                            {explanation.ai_reasoning}
                        </p>
                    </div>
                )}

                {/* Selected Reasons vs Rejected */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-emerald-50/50 p-4 rounded-2xl border border-emerald-100/50">
                        <h4 className="flex items-center gap-2 text-sm font-bold text-emerald-700 mb-3">
                            <CheckCircle2 size={16} />
                            Strengths
                        </h4>
                        <ul className="space-y-2">
                            {explanation.selected_reasons.map((reason, i) => (
                                <li key={i} className="text-xs text-emerald-600 flex items-start gap-2">
                                    <span className="mt-0.5">•</span>
                                    <span>{reason}</span>
                                </li>
                            ))}
                            {explanation.selected_reasons.length === 0 && (
                                <li className="text-xs text-emerald-500/60 italic">No major strengths highlighted.</li>
                            )}
                        </ul>
                    </div>

                    <div className="bg-rose-50/50 p-4 rounded-2xl border border-rose-100/50">
                        <h4 className="flex items-center gap-2 text-sm font-bold text-rose-700 mb-3">
                            <XCircle size={16} />
                            Concerns
                        </h4>
                        <ul className="space-y-2">
                            {explanation.rejected_reasons.map((reason, i) => (
                                <li key={i} className="text-xs text-rose-600 flex items-start gap-2">
                                    <span className="mt-0.5">•</span>
                                    <span>{reason}</span>
                                </li>
                            ))}
                            {explanation.rejected_reasons.length === 0 && (
                                <li className="text-xs text-rose-500/60 italic">No major concerns found.</li>
                            )}
                        </ul>
                    </div>
                </div>

            </div>
        </div>
    );
}
