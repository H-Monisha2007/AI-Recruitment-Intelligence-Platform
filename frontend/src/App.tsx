import { useState, useEffect } from 'react';
import { useAuthStore } from './store/authStore';
import AuthPage from './pages/AuthPage';
import RecruiterDashboard from './pages/RecruiterDashboard';
import {
  FileText, Activity, Brain, LayoutDashboard,
  LogOut, User as UserIcon, HelpCircle, ChevronRight,
  Menu, X, Bell
} from 'lucide-react';
import { rolesApi, reportsApi } from './services/api';
import { RoleInfo, AnalysisResult } from './types';
import AnalyzeMode from './components/AnalyzeMode.tsx';
import Dashboard from './components/Dashboard.tsx';
import { Button } from './components/ui/Button.tsx';

export default function App() {
  const { user, isAuthenticated, clearAuth } = useAuthStore();
  const [activeTab, setActiveTab] = useState('analyze');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [roles, setRoles] = useState<RoleInfo[]>([]);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      rolesApi.list().then(res => setRoles(res.roles)).catch(console.error);
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) return <AuthPage />;

  const navigation = [
    { id: 'dashboard', name: 'Dashboard', icon: LayoutDashboard, roles: ['recruiter', 'admin'] },
    { id: 'analyze', name: 'Analyze Resume', icon: FileText, roles: ['candidate', 'recruiter', 'admin'] },
    { id: 'train', name: 'Training Studio', icon: Brain, roles: ['recruiter', 'admin'] },
    { id: 'history', name: 'My History', icon: Clock, roles: ['candidate'] },
  ];

  const filteredNav = navigation.filter(n => n.roles.includes(user?.role || ''));

  return (
    <div className="flex h-screen bg-zinc-100 font-sans text-zinc-900 overflow-hidden">
      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-72 bg-black text-white transition-all duration-300 ease-in-out transform
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:relative lg:translate-x-0
      `}>
        <div className="flex flex-col h-full">
          <div className="p-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center p-0.5 shadow-lg shadow-white/5">
                <div className="w-full h-full bg-black rounded-[10px] flex items-center justify-center">
                  <Brain className="text-white" size={24} />
                </div>
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">
                  Talent Scout
                </h1>
                <p className="text-[10px] font-black tracking-widest text-zinc-500 uppercase">Pro Edition X</p>
              </div>
            </div>
          </div>

          <nav className="flex-1 px-4 space-y-2">
            {filteredNav.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setAnalysisResult(null);
                }}
                className={`
                  w-full flex items-center px-4 py-3 rounded-2xl transition-all duration-200 group
                  ${activeTab === item.id
                    ? 'bg-white text-black shadow-lg shadow-white/10'
                    : 'text-zinc-500 hover:text-white hover:bg-white/5'}
                `}
              >
                <item.icon size={20} className={activeTab === item.id ? 'text-black' : 'text-zinc-500 group-hover:text-white'} />
                <span className="ml-3 font-bold text-sm">{item.name}</span>
                {activeTab === item.id && <ChevronRight size={16} className="ml-auto opacity-50" />}
              </button>
            ))}
          </nav>

          <div className="p-6 border-t border-white/5 mt-auto">
            <div className="flex items-center gap-3 mb-6 p-4 rounded-[1.5rem] bg-white/5 border border-white/5">
              <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center text-black font-black text-xl border border-white/20">
                {user?.full_name.charAt(0)}
              </div>
              <div className="flex-1 overflow-hidden">
                <p className="text-sm font-black truncate">{user?.full_name}</p>
                <p className="text-[10px] text-zinc-500 uppercase tracking-[0.2em] font-black">{user?.role}</p>
              </div>
            </div>
            <Button
              onClick={clearAuth}
              variant="ghost"
              className="w-full text-rose-400 border-transparent hover:bg-rose-400/5 hover:text-rose-500 hover:border-transparent"
              icon={<LogOut size={18} />}
            >
              Sign Out
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Area */}
      <main className="flex-1 flex flex-col min-w-0 bg-white lg:rounded-l-[2.5rem] lg:shadow-2xl lg:my-4 lg:mr-4 border-l border-zinc-100 overflow-hidden relative">
        {/* Header */}
        <header className="h-20 border-b border-zinc-50 flex items-center justify-between px-8 bg-white/50 backdrop-blur-md sticky top-0 z-40">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="lg:hidden p-2 text-zinc-500 hover:bg-zinc-100 rounded-xl"
          >
            {isSidebarOpen ? <X /> : <Menu />}
          </button>

          <div className="flex items-center gap-4 ml-auto">
            <button className="p-2 text-zinc-400 hover:text-zinc-600 transition-colors relative">
              <Bell size={20} />
              <span className="absolute top-2 right-2 w-2 h-2 bg-black rounded-full border-2 border-white"></span>
            </button>
            <div className="h-8 w-[1px] bg-zinc-100 mx-2"></div>
            <div className="flex items-center gap-3 cursor-pointer group">
              <div className="text-right">
                <p className="text-sm font-bold text-zinc-800">{user?.full_name}</p>
                <p className="text-[10px] text-zinc-400 font-medium">Standard License</p>
              </div>
              <div className="w-10 h-10 rounded-xl bg-zinc-100 flex items-center justify-center text-zinc-500 font-bold border border-zinc-200 group-hover:border-black transition-colors">
                <UserIcon size={20} />
              </div>
            </div>
          </div>
        </header>

        {/* Content Container */}
        <div className="flex-1 overflow-auto p-4 lg:p-10 scrollbar-hide">
          <div className="max-w-7xl mx-auto h-full">
            {activeTab === 'dashboard' && <RecruiterDashboard />}
            {activeTab === 'analyze' && !analysisResult && (
              <AnalyzeMode
                roles={roles}
                onResult={(res: AnalysisResult) => setAnalysisResult(res)}
              />
            )}
            {activeTab === 'analyze' && analysisResult && (
              <Dashboard
                results={analysisResult}
                onReset={() => setAnalysisResult(null)}
                onDownloadPdf={async () => {
                  const blob = await reportsApi.generatePdf(analysisResult as any);
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `AI_Talent_Scout_${Date.now()}.pdf`;
                  a.click();
                }}
              />
            )}
            {activeTab === 'train' && <TrainMode />}
            {activeTab === 'history' && <HistoryMode />}
          </div>
        </div>

        {/* Floating Help */}
        <button className="fixed bottom-10 right-10 w-14 h-14 bg-black text-white rounded-full flex items-center justify-center shadow-2xl hover:scale-110 transition-transform z-50 border-4 border-white">
          <HelpCircle size={24} />
        </button>
      </main>
    </div>
  );
}

// ── Placeholder Components for build-safety ────────────────────────────────

function Clock({ size, className }: any) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

function TrainMode() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center">
      <div className="w-20 h-20 bg-zinc-100 rounded-3xl flex items-center justify-center mb-6">
        <Brain className="text-black" size={40} />
      </div>
      <h2 className="text-2xl font-bold mb-2 text-zinc-800">ML Training Studio</h2>
      <p className="text-zinc-500 max-w-md">Coming soon: Pro-tier fine-tuning of embedding models on your custom datasets.</p>
    </div>
  );
}

function HistoryMode() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center">
      <div className="w-20 h-20 bg-zinc-100 rounded-3xl flex items-center justify-center mb-6">
        <Clock size={40} className="text-black" />
      </div>
      <h2 className="text-2xl font-bold mb-2 text-zinc-800">Analysis History</h2>
      <p className="text-zinc-500 max-w-md">Access your previous resume assessments and improvement recommendations here.</p>
    </div>
  );
}
