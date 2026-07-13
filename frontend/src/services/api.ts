import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
    baseURL: `${BASE_URL}/api/v1`,
    timeout: 60000,
})

// Attach JWT token from localStorage
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Auto-logout on 401
api.interceptors.response.use(
    (res) => res,
    (err) => {
        if (err.response?.status === 401) {
            localStorage.removeItem('access_token')
            localStorage.removeItem('user')
            window.location.href = '/login'
        }
        return Promise.reject(err)
    }
)

// ── Auth ─────────────────────────────────────────────────────────────────────

export const authApi = {
    register: (data: { email: string; password: string; full_name: string; role: string }) =>
        api.post('/auth/register', data).then((r) => r.data),

    login: (email: string, password: string) =>
        api.post('/auth/login', { email, password }).then((r) => r.data),

    me: () => api.get('/auth/me').then((r) => r.data),
}

// ── Resumes ──────────────────────────────────────────────────────────────────

export const resumeApi = {
    analyze: (file: File, selectedRole: string) => {
        const form = new FormData()
        form.append('file', file)
        form.append('selected_role', selectedRole)
        form.append('save_result', 'true')
        return api.post('/resumes/analyze', form, {
            headers: { 'Content-Type': 'multipart/form-data' },
        }).then((r) => r.data)
    },

    upload: (file: File) => {
        const form = new FormData()
        form.append('file', file)
        return api.post('/resumes/upload', form, {
            headers: { 'Content-Type': 'multipart/form-data' },
        }).then((r) => r.data)
    },

    list: () => api.get('/resumes/').then((r) => r.data),

    skillGap: (resume_text: string, job_skills: string[]) =>
        api.post('/resumes/skill-gap', { resume_text, job_skills }).then((r) => r.data),
}

// ── Roles ─────────────────────────────────────────────────────────────────────

export const rolesApi = {
    list: () => api.get('/roles/').then((r) => r.data),
}

// ── Reports ──────────────────────────────────────────────────────────────────

export const reportsApi = {
    generatePdf: async (data: Record<string, unknown>): Promise<Blob> => {
        const resp = await api.post('/reports/', data, { responseType: 'blob' })
        return resp.data
    },
}

// ── ML Training ───────────────────────────────────────────────────────────────

export const trainApi = {
    train: (file: File) => {
        const form = new FormData()
        form.append('file', file)
        return api.post('/train/', form, {
            headers: { 'Content-Type': 'multipart/form-data' },
        }).then((r) => r.data)
    },
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export const analyticsApi = {
    dashboard: () => api.get('/analytics/dashboard').then((r) => r.data),
}
