// Shared TypeScript types

export interface User {
    id: string
    email: string
    full_name: string
    role: 'admin' | 'recruiter' | 'candidate'
    is_active: boolean
    is_verified: boolean
    created_at: string
}

export interface RoleInfo {
    name: string
    skills: string[]
    min_experience: number
    color: string
}

export interface ResumeReview {
    sections_found: string[]
    has_contact: boolean
    action_verbs: number
    has_quant: boolean
    word_count: number
    length_status: string
    tech_stack: string[]
    has_github: boolean
    has_portfolio: boolean
}

export interface ExplanationData {
    selected_reasons: string[]
    rejected_reasons: string[]
    matched_skills: string[]
    missing_skills: string[]
    ai_reasoning?: string
}

export interface AnalysisResult {
    success: boolean
    ats_score_id?: string
    ml_score: number
    skill_similarity: number
    semantic_score: number
    ats_score: number
    role_fit: number
    experience: number
    role: string
    top_roles: [string, number][]
    role_data: { skills: string[]; exp: number; color: string }
    resume_preview: string
    full_resume: string
    predicted_role?: string
    model_confidence?: number
    top3_preds: [string, number][]
    resume_review: ResumeReview
    found_skills: string[]
    missing_skills: string[]
    hire_prob: number
    confidence: number
    decision: string
    explanation: ExplanationData
}

export interface TrainMetrics {
    Model: string
    Accuracy: string
    Precision: string
    Recall: string
    F1_Score: string
}

export interface TrainResult {
    success: boolean
    message: string
    metrics: TrainMetrics[]
    best_model: string
    training_time_seconds?: number
}

export interface DashboardStats {
    total_resumes_analyzed: number
    total_users: number
    avg_role_fit: number
    avg_ats_score: number
    top_roles_distribution: Record<string, unknown>[]
    decisions_breakdown: Record<string, number>
    recent_analyses: {
        candidate: string
        email: string
        role_fit: number
        decision: string
        ats_score: number
        created_at: string
    }[]
}

export interface SkillGapResult {
    success: boolean
    found_skills: string[]
    missing_skills: string[]
    coverage_percent: number
    recommendations: string[]
}
