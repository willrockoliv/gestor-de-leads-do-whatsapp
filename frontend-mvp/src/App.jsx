import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  Sun, Moon, RefreshCw, MessageCircle, Flame, Snowflake, 
  Thermometer, AlertCircle, Clock, ArrowRight, Sparkles, 
  Send, User, LayoutList, X, LogIn, Lock, Mail, Loader2
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

// --- UTILITÁRIOS ---
const formatRelativeTime = (dateString) => {
  if (!dateString) return 'Sem data';
  const date = new Date(dateString);
  const now = new Date();
  const diffInMinutes = Math.floor((now - date) / 1000 / 60);
  
  if (diffInMinutes < 1) return 'Agora mesmo';
  if (diffInMinutes < 60) return `${diffInMinutes} min atrás`;
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours}h atrás`;
  const diffInDays = Math.floor(diffInHours / 24);
  return `${diffInDays} dias atrás`;
};

// --- COMPONENTES PRINCIPAIS ---
export default function App() {
  const [token, setToken] = useState(localStorage.getItem('leadiq_token') || null);
  // Garante que todo o app inicie no dark mode se renderizar direto aqui
  const [theme, setTheme] = useState('dark'); 

  // Se não houver token, exibe a tela de Login
  if (!token) {
    return <LoginView setToken={setToken} theme={theme} setTheme={setTheme} />;
  }

  // Se houver token, exibe o Dashboard
  return <DashboardView token={token} setToken={setToken} theme={theme} setTheme={setTheme} />;
}

// --- TELA DE LOGIN ---
function LoginView({ setToken, theme }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const formData = new URLSearchParams();
      formData.append('username', email); 
      formData.append('password', password);

      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });

      if (!res.ok) throw new Error('Credenciais inválidas ou erro no servidor.');

      const data = await res.json();
      localStorage.setItem('leadiq_token', data.access_token);
      setToken(data.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={theme}>
      <div className="min-h-screen bg-slate-50 dark:bg-[#0B1120] flex items-center justify-center p-4 transition-colors duration-300">
        <div className="max-w-md w-full bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 p-8">
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-teal-600 flex items-center justify-center shadow-lg shadow-teal-500/30 mb-4">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">LeadIQ Dashboard</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-2 text-center">Entre para gerenciar seus leads do WhatsApp</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Email</label>
              <div className="relative">
                <Mail className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  type="email" required
                  value={email} onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none text-slate-900 dark:text-white transition-all"
                  placeholder="seu@email.com"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Senha</label>
              <div className="relative">
                <Lock className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  type="password" required
                  value={password} onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-teal-500 outline-none text-slate-900 dark:text-white transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {error && <div className="p-3 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-sm rounded-lg border border-red-100 dark:border-red-500/20">{error}</div>}

            <button 
              type="submit" disabled={loading}
              className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 dark:bg-teal-600 dark:hover:bg-teal-500 text-white rounded-xl font-medium shadow-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <LogIn className="w-5 h-5" />}
              Entrar no Painel
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// --- DASHBOARD PRINCIPAL ---
function DashboardView({ token, setToken, theme, setTheme }) {
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState(null);
  
  const [selectedLeadId, setSelectedLeadId] = useState(null);
  const [selectedLeadDetails, setSelectedLeadDetails] = useState(null);
  
  const [isGlobalProcessing, setIsGlobalProcessing] = useState(false);
  const [activeStage, setActiveStage] = useState("Todos");
  const [isLoadingInitial, setIsLoadingInitial] = useState(true);

  const pollers = useRef({}); 
  const globalPoller = useRef(null);

  const handleLogout = () => {
    localStorage.removeItem('leadiq_token');
    setToken(null);
  };

  const authHeaders = useMemo(() => ({
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }), [token]);

  const fetchData = async () => {
    try {
      const statsRes = await fetch(`${API_BASE_URL}/dashboard/stats`, { headers: authHeaders });
      if (statsRes.ok) {
        setStats(await statsRes.json());
      } else if (statsRes.status === 401) {
        handleLogout();
        return;
      }

      const leadsRes = await fetch(`${API_BASE_URL}/leads?status=active&page_size=100`, { headers: authHeaders });
      if (leadsRes.ok) {
        const data = await leadsRes.json();
        setLeads(data);
      }
    } catch (error) {
      console.error("Erro ao buscar dados", error);
    } finally {
      setIsLoadingInitial(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!selectedLeadId) {
      setSelectedLeadDetails(null);
      return;
    }

    const fetchLeadDetail = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/leads/${selectedLeadId}`, { headers: authHeaders });
        if (res.ok) {
          const data = await res.json();
          setSelectedLeadDetails(data);
        }
      } catch (error) {
        console.error("Erro ao buscar detalhes do lead", error);
      }
    };

    fetchLeadDetail();
  }, [selectedLeadId, authHeaders]);

  const toggleTheme = () => setTheme(theme === 'light' ? 'dark' : 'light');

  const FUNNEL_STAGES = useMemo(() => {
    const stages = new Set(leads.map(l => l.current_stage).filter(Boolean));
    return ["Todos", ...Array.from(stages).sort()];
  }, [leads]);

  const filteredLeads = useMemo(() => {
    let filtered = leads;
    if (activeStage !== "Todos") {
      filtered = leads.filter(l => l.current_stage === activeStage);
    }
    return filtered.sort((a, b) => (b.temperature_score || 0) - (a.temperature_score || 0));
  }, [leads, activeStage]);

  const handleAnalyzeSingle = async (id) => {
    try {
      setLeads(prev => prev.map(l => l.id === id ? { ...l, is_processing: true } : l));
      if (selectedLeadDetails?.id === id) {
        setSelectedLeadDetails(prev => ({ ...prev, is_processing: true }));
      }

      const res = await fetch(`${API_BASE_URL}/leads/${id}/analyze`, { method: 'POST', headers: authHeaders });
      if (!res.ok && res.status !== 202) throw new Error("Falha ao iniciar análise");

      if (pollers.current[id]) clearInterval(pollers.current[id]);
      
      pollers.current[id] = setInterval(async () => {
        const statusRes = await fetch(`${API_BASE_URL}/leads/${id}/analyze/status`, { headers: authHeaders });
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          if (statusData.analysis_status === 'completed' || statusData.analysis_status === 'failed') {
            clearInterval(pollers.current[id]);
            fetchData();
            if (selectedLeadId === id) {
              const detailRes = await fetch(`${API_BASE_URL}/leads/${id}`, { headers: authHeaders });
              if (detailRes.ok) setSelectedLeadDetails(await detailRes.json());
            }
          }
        }
      }, 2500);
    } catch (err) {
      console.error(err);
      fetchData();
    }
  };

  const handleAnalyzeAll = async () => {
    try {
      setIsGlobalProcessing(true);
      const res = await fetch(`${API_BASE_URL}/leads/analyze-all`, { method: 'POST', headers: authHeaders });
      if (!res.ok && res.status !== 202) throw new Error("Falha ao iniciar análise em lote");

      if (globalPoller.current) clearInterval(globalPoller.current);
      
      globalPoller.current = setInterval(async () => {
        const statusRes = await fetch(`${API_BASE_URL}/leads/analyze/status`, { headers: authHeaders });
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          if (statusData.counts.pending === 0 && statusData.counts.processing === 0) {
            clearInterval(globalPoller.current);
            setIsGlobalProcessing(false);
            fetchData();
          }
        }
      }, 3000);
    } catch (err) {
      console.error(err);
      setIsGlobalProcessing(false);
    }
  };

  const getTemperatureBadge = (temp) => {
    const t = temp || 0;
    if (t >= 70) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-teal-50 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400 border border-teal-100 dark:border-teal-500/20">
          <Flame className="w-3.5 h-3.5" /> Quente ({t})
        </span>
      );
    }
    if (t >= 40) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400 border border-blue-100 dark:border-blue-500/20">
          <Thermometer className="w-3.5 h-3.5" /> Morno ({t})
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-600 dark:bg-slate-800/50 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
        <Snowflake className="w-3.5 h-3.5" /> Frio ({t})
      </span>
    );
  };

  const easeTransition = "transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)]";

  if (isLoadingInitial) {
    return (
      <div className={theme}>
        <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#0B1120] text-slate-900 dark:text-white transition-colors duration-300">
          <Loader2 className="w-8 h-8 animate-spin text-teal-500" />
        </div>
      </div>
    );
  }

  return (
    <div className={theme}>
      <div className="min-h-screen bg-slate-50 dark:bg-[#0B1120] text-slate-900 dark:text-slate-50 font-sans transition-colors duration-300 overflow-x-hidden">
        
        {/* HEADER */}
        <header className="sticky top-0 z-20 bg-white/80 dark:bg-[#0B1120]/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800/60">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-slate-900 dark:bg-slate-100 flex items-center justify-center shadow-sm">
                <Sparkles className="w-5 h-5 text-white dark:text-slate-900" />
              </div>
              <span className="font-semibold text-lg tracking-tight">LeadIQ</span>
            </div>

            <div className="flex items-center gap-4">
              <button 
                onClick={toggleTheme}
                className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800/50 transition-colors text-slate-500 dark:text-slate-400"
              >
                {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
              </button>
              
              <div className="h-6 w-px bg-slate-200 dark:bg-slate-800"></div>
              
              <button onClick={handleLogout} className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center ring-2 ring-white dark:ring-[#0B1120]">
                  <User className="w-4 h-4 text-slate-600 dark:text-slate-300" />
                </div>
              </button>
            </div>
          </div>
        </header>

        {/* CONTEÚDO PRINCIPAL */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">Caixa de Entrada</h1>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Gerencie e priorize seus leads com inteligência.</p>
            </div>
            
            <button
              onClick={handleAnalyzeAll}
              disabled={isGlobalProcessing}
              className="inline-flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-lg text-sm font-medium shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`w-4 h-4 ${isGlobalProcessing ? 'animate-spin' : ''}`} />
              {isGlobalProcessing ? 'Processando Fila...' : 'Atualizar Todos (IA)'}
            </button>
          </div>

          {/* KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
            <div className="bg-white dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none backdrop-blur-sm">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-4">
                <span className="text-sm font-medium">Leads Ativos</span>
                <MessageCircle className="w-4 h-4" />
              </div>
              <span className="text-3xl font-semibold text-slate-900 dark:text-slate-50">
                {stats?.total_active || 0}
              </span>
            </div>
            
            <div className="bg-white dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none backdrop-blur-sm">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-4">
                <span className="text-sm font-medium">Prioridade Alta (Quentes)</span>
                <Flame className="w-4 h-4 text-teal-600 dark:text-teal-400" />
              </div>
              <span className="text-3xl font-semibold text-slate-900 dark:text-slate-50">
                {leads.filter(l => (l.temperature_score || 0) >= 70).length}
              </span>
            </div>

            <div className="bg-white dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none backdrop-blur-sm">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-4">
                <span className="text-sm font-medium">Temp. Média Geral</span>
                <Thermometer className="w-4 h-4" />
              </div>
              <span className="text-3xl font-semibold text-slate-900 dark:text-slate-50">
                {stats?.avg_temperature ? Math.round(stats.avg_temperature) : 0}°
              </span>
            </div>
          </div>

          {/* LAYOUT FLEXÍVEL (Lista vs Detalhes) */}
          <div className="flex flex-col lg:flex-row items-start w-full relative">
            
            {/* ESQUERDA: Abas e Lista */}
            <div className={`${easeTransition} flex flex-col gap-4 flex-shrink-0 ${selectedLeadId ? 'w-full lg:w-[42%] lg:pr-6' : 'w-full'}`}>
              
              {/* TABS DE FUNIL */}
              <div className="bg-slate-200/60 dark:bg-[#131C2D] rounded-xl p-1.5 flex overflow-x-auto hide-scrollbar gap-1 border border-slate-200/50 dark:border-slate-800/50 shadow-inner">
                {FUNNEL_STAGES.map((stage) => {
                  const isActive = activeStage === stage;
                  const count = stage === "Todos" 
                    ? leads.length 
                    : leads.filter(l => l.current_stage === stage).length;

                  return (
                    <button
                      key={stage}
                      onClick={() => setActiveStage(stage)}
                      className={`
                        relative flex-1 min-w-[120px] flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 ease-out whitespace-nowrap
                        ${isActive 
                          ? 'bg-white dark:bg-[#1E293B] text-slate-900 dark:text-slate-50 shadow-sm ring-1 ring-slate-900/5 dark:ring-white/5' 
                          : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-800/30'
                        }
                      `}
                    >
                      {stage || 'Sem Etapa'}
                      <span className={`
                        px-1.5 py-0.5 rounded-md text-xs
                        ${isActive 
                          ? 'bg-slate-100 dark:bg-slate-700/50 text-slate-600 dark:text-slate-300' 
                          : 'bg-slate-200/50 dark:bg-slate-800/40 text-slate-400 dark:text-slate-500'
                        }
                      `}>
                        {count}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* LISTA */}
              <div className="flex flex-col gap-3 mt-2">
                {filteredLeads.length > 0 ? (
                  filteredLeads.map((lead) => (
                    <button
                      key={lead.id}
                      onClick={() => setSelectedLeadId(selectedLeadId === lead.id ? null : lead.id)} 
                      className={`text-left p-5 rounded-2xl border transition-all duration-300 transform origin-top group relative overflow-hidden ${
                        selectedLeadId === lead.id 
                          ? 'bg-white dark:bg-slate-900 border-teal-500/40 dark:border-teal-500/40 shadow-md ring-1 ring-teal-500/10 dark:ring-teal-500/20' 
                          : 'bg-white/60 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800/60 hover:border-slate-300 dark:hover:border-slate-700 shadow-sm hover:shadow dark:hover:bg-slate-900/80'
                      }`}
                    >
                      {lead.is_processing && (
                        <div className="absolute inset-0 bg-slate-50/50 dark:bg-slate-900/50 backdrop-blur-[1px] flex items-center justify-center z-10">
                          <Loader2 className="w-5 h-5 animate-spin text-teal-500" />
                        </div>
                      )}

                      <div className="flex justify-between items-start mb-4 relative z-0">
                        <div>
                          <h3 className={`font-semibold transition-colors ${selectedLeadId === lead.id ? 'text-teal-700 dark:text-teal-400' : 'text-slate-900 dark:text-slate-50'}`}>
                            {lead.name || 'Lead sem nome'}
                          </h3>
                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-mono">{lead.phone}</p>
                        </div>
                        {getTemperatureBadge(lead.temperature_score)}
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mt-2 pt-4 border-t border-slate-100 dark:border-slate-800/60 relative z-0">
                        <span className={`flex items-center gap-1.5 px-2 py-1 rounded-md font-medium transition-colors ${
                          selectedLeadId === lead.id ? 'bg-teal-50 dark:bg-teal-500/10 text-teal-700 dark:text-teal-400' : 'bg-slate-100 dark:bg-slate-800/50'
                        }`}>
                          <LayoutList className="w-3.5 h-3.5 opacity-70" />
                          {lead.current_stage || 'Nova Mensagem'}
                        </span>
                        <span className="flex items-center gap-1.5 font-medium opacity-80">
                          <Clock className="w-3.5 h-3.5" /> {formatRelativeTime(lead.updated_at)}
                        </span>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="text-center py-16 px-4 border border-dashed border-slate-300 dark:border-slate-800 rounded-2xl bg-white/30 dark:bg-slate-900/20">
                    <LayoutList className="w-10 h-10 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
                    <p className="text-slate-500 dark:text-slate-400 font-medium">Nenhum lead encontrado.</p>
                  </div>
                )}
              </div>
            </div>

            {/* DIREITA: Detalhes e IA */}
            <div 
              className={`${easeTransition} overflow-hidden lg:pl-2 ${
                selectedLeadId 
                  ? 'w-full lg:w-[58%] opacity-100 max-h-[3000px] mt-8 lg:mt-0' 
                  : 'w-0 opacity-0 max-h-0 lg:max-h-[3000px] m-0 p-0'
              }`}
            >
              <div className="w-full lg:w-[calc(100vw*0.58-2rem)] lg:max-w-[700px] xl:max-w-[800px] pb-8">
                {selectedLeadDetails ? (
                  <div className="bg-white dark:bg-slate-900/95 rounded-2xl border border-slate-200 dark:border-slate-800/80 shadow-xl dark:shadow-[0_8px_30px_rgb(0,0,0,0.2)] overflow-hidden flex flex-col min-h-[500px]">
                    
                    {/* Header do Lead */}
                    <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/50">
                      <div>
                        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-50 tracking-tight">
                          {selectedLeadDetails.name || 'Lead sem nome'}
                        </h2>
                        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 font-mono">
                          {selectedLeadDetails.phone}
                        </p>
                      </div>
                      
                      <div className="flex items-center gap-4">
                        <div className="text-right hidden sm:block">
                          <p className="text-[10px] text-slate-400 uppercase tracking-wider font-bold mb-1">Score IA</p>
                          {getTemperatureBadge(selectedLeadDetails.temperature_score)}
                        </div>
                        
                        <div className="flex items-center gap-2 border-l border-slate-200 dark:border-slate-700 pl-4">
                          <button 
                            onClick={() => handleAnalyzeSingle(selectedLeadDetails.id)}
                            disabled={selectedLeadDetails.is_processing || isGlobalProcessing}
                            className="p-2 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800 hover:shadow-sm transition-all disabled:opacity-50 group"
                            title="Reanalisar Lead"
                          >
                            <RefreshCw className={`w-4 h-4 group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors ${selectedLeadDetails.is_processing ? 'animate-spin text-teal-600 dark:text-teal-400' : ''}`} />
                          </button>
                          
                          <button 
                            onClick={() => setSelectedLeadId(null)}
                            className="p-2 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                            title="Fechar detalhes"
                          >
                            <X className="w-5 h-5" />
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Insights Gerados pela LLM */}
                    <div className="p-6 md:p-8 flex-1 flex flex-col gap-8 relative">
                      
                      {selectedLeadDetails.is_processing && (
                        <div className="absolute inset-0 z-10 bg-white/70 dark:bg-[#0B1120]/60 backdrop-blur-sm flex items-center justify-center">
                          <div className="flex flex-col items-center gap-4 bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-700">
                            <Loader2 className="w-8 h-8 animate-spin text-teal-600 dark:text-teal-400" />
                            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">A IA está analisando a conversa...</span>
                          </div>
                        </div>
                      )}

                      {/* Verifica se já existe análise */}
                      {selectedLeadDetails.latest_analysis ? (
                        <>
                          <div className="space-y-3">
                            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 flex items-center gap-2 uppercase tracking-widest">
                              <MessageCircle className="w-4 h-4" /> Resumo da Conversa
                            </h3>
                            <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed bg-slate-50 dark:bg-slate-800/30 p-5 rounded-xl border border-slate-100 dark:border-slate-800/50 shadow-sm whitespace-pre-line">
                              {selectedLeadDetails.latest_analysis.conversation_summary}
                            </p>
                          </div>

                          <div className="space-y-3">
                            <h3 className="text-xs font-bold text-teal-600 dark:text-teal-400 flex items-center gap-2 uppercase tracking-widest">
                              <Sparkles className="w-4 h-4" /> Dica Estratégica
                            </h3>
                            <div className="flex items-start gap-3 bg-teal-50/80 dark:bg-teal-900/20 p-5 rounded-xl border border-teal-100 dark:border-teal-500/20 shadow-sm">
                              <AlertCircle className="w-5 h-5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                              <p className="text-teal-900 dark:text-teal-100 text-sm leading-relaxed whitespace-pre-line">
                                {selectedLeadDetails.latest_analysis.qualitative_tips}
                              </p>
                            </div>
                          </div>

                          <div className="space-y-3 mt-auto pt-4">
                            <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 flex items-center gap-2 uppercase tracking-widest">
                              <Send className="w-4 h-4" /> Sugestão de Resposta
                            </h3>
                            <div className="bg-slate-900 dark:bg-[#0B1120] p-5 md:p-6 rounded-xl shadow-inner relative group border border-slate-800 dark:border-slate-800/80">
                              <p className="text-slate-200 dark:text-slate-300 text-sm leading-relaxed font-medium italic whitespace-pre-line">
                                "{selectedLeadDetails.latest_analysis.suggested_reply}"
                              </p>
                            </div>
                          </div>
                        </>
                      ) : (
                        <div className="flex flex-col items-center justify-center flex-1 py-12 text-center opacity-60">
                          <Sparkles className="w-12 h-12 text-slate-400 mb-4" />
                          <p className="text-slate-600 dark:text-slate-300 font-medium">Nenhuma análise gerada para este lead ainda.</p>
                          <p className="text-sm text-slate-500 mt-1">Clique no botão de atualizar acima para processar as mensagens.</p>
                        </div>
                      )}
                    </div>

                    {/* Footer / Ações */}
                    <div className="p-6 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                      <button 
                        onClick={() => {
                          const reply = selectedLeadDetails.latest_analysis?.suggested_reply || '';
                          const phone = selectedLeadDetails.phone.replace(/\D/g, '');
                          window.open(`https://wa.me/${phone}?text=${encodeURIComponent(reply)}`, '_blank');
                        }}
                        disabled={selectedLeadDetails.is_processing || !selectedLeadDetails.latest_analysis}
                        className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white dark:bg-teal-600 dark:hover:bg-teal-500 dark:text-white px-6 py-3 rounded-xl text-sm font-semibold shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-md hover:-translate-y-0.5"
                      >
                        Enviar no WhatsApp <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>

                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full min-h-[500px]">
                    <Loader2 className="w-8 h-8 animate-spin text-teal-500" />
                  </div>
                )}
              </div>
            </div>

          </div>
        </main>
      </div>
    </div>
  );
}
