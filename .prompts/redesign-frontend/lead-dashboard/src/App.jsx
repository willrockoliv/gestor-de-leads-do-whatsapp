import React, { useState, useEffect, useMemo } from 'react';
import { 
  Sun, Moon, RefreshCw, MessageCircle, Flame, Snowflake, 
  Thermometer, CheckCircle2, AlertCircle, Clock, Search, Filter, 
  ArrowRight, Sparkles, Send, User, LayoutList, X
} from 'lucide-react';

// --- MOCK DATA ---
const INITIAL_LEADS = [
  {
    id: 1,
    name: "Carlos Mendes",
    number: "+55 11 99999-1111",
    stage: "Descoberta",
    temperature: 85,
    summary: "O lead viu o anúncio de consultoria no Instagram e tem urgência. O faturamento da empresa dele travou nos últimos 3 meses e ele precisa de ajuda para estruturar o comercial. Tem orçamento aprovado.",
    tip: "Foque no ROI rápido. Ele está ansioso, então mostre um case de sucesso de estruturação comercial em menos de 30 dias.",
    suggestedReply: "Olá, Carlos! Vi que você precisa destravar o faturamento com urgência. Nós conseguimos estruturar a base do seu comercial em até 15 dias. Quer agendar uma call rápida amanhã às 14h para eu te mostrar como?",
    lastMessageAt: "10 min atrás",
    isProcessing: false,
  },
  {
    id: 2,
    name: "Mariana Costa",
    number: "+55 11 99999-2222",
    stage: "Orçamento Enviado",
    temperature: 45,
    summary: "Solicitou o catálogo de serviços, mas achou o pacote premium caro. Perguntou se fazemos um desconto ou se há uma opção mais enxuta.",
    tip: "Não dê desconto imediato. Ofereça um 'downsell' com o pacote básico para não desvalorizar o serviço principal.",
    suggestedReply: "Oi, Mariana. Entendo perfeitamente a questão do orçamento. Como alternativa, temos o Pacote Essencial, que foca apenas no que você precisa para começar agora, com um investimento 30% menor. Faz sentido dar uma olhada nesse formato?",
    lastMessageAt: "2 horas atrás",
    isProcessing: false,
  },
  {
    id: 3,
    name: "Roberto Silva (Construtora)",
    number: "+55 11 99999-3333",
    stage: "Em Negociação",
    temperature: 95,
    summary: "Lead extremamente qualificado. Já validou a proposta técnica e agora está apenas tirando dúvidas contratuais com o jurídico. Pediu para confirmarmos a data de início.",
    tip: "Acelere o fechamento. Envie o contrato atualizado e já sugira a data de kickoff para criar compromisso.",
    suggestedReply: "Roberto, tudo certo por aqui. O jurídico já liberou o contrato atualizado. Podemos colocar o kickoff (reunião inicial) para a próxima segunda-feira às 10h? Se sim, já te mando o link para assinatura digital.",
    lastMessageAt: "1 min atrás",
    isProcessing: false,
  },
  {
    id: 4,
    name: "Juliana (Loja de Roupas)",
    number: "+55 11 99999-4444",
    stage: "Descoberta",
    temperature: 15,
    summary: "Mandou apenas 'Oi, qual o valor?'. Não respondeu às perguntas de qualificação e parou de interagir há dois dias.",
    tip: "Lead desengajado. Faça uma última tentativa de reativação gerando curiosidade, caso contrário, mova para 'Perdido'.",
    suggestedReply: "Oi, Juliana! Para te passar o valor exato, eu precisava entender um detalhe do seu negócio. Você ainda está buscando aumentar as vendas da loja este mês?",
    lastMessageAt: "2 dias atrás",
    isProcessing: false,
  }
];

// Ordem lógica do funil
const FUNNEL_STAGES = ["Todos", "Descoberta", "Orçamento Enviado", "Em Negociação"];

export default function App() {
  const [theme, setTheme] = useState('dark'); // Inicia no dark mode para combinar com os prints
  const [leads, setLeads] = useState(INITIAL_LEADS);
  
  // Começamos com null para a tela iniciar expandida
  const [selectedLeadId, setSelectedLeadId] = useState(null); 
  
  const [isGlobalProcessing, setIsGlobalProcessing] = useState(false);
  const [activeStage, setActiveStage] = useState("Todos");

  // Toggle Theme
  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  // Helper para Badge de Temperatura
  const getTemperatureBadge = (temp) => {
    if (temp >= 70) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-teal-50 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400">
          <Flame className="w-3.5 h-3.5" /> Quente ({temp})
        </span>
      );
    }
    if (temp >= 40) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400">
          <Thermometer className="w-3.5 h-3.5" /> Morno ({temp})
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-600 dark:bg-slate-800/50 dark:text-slate-300">
        <Snowflake className="w-3.5 h-3.5" /> Frio ({temp})
      </span>
    );
  };

  // Simulação de chamadas "Lock" no Backend
  const handleAnalyzeSingle = (id) => {
    setLeads(prev => prev.map(l => l.id === id ? { ...l, isProcessing: true } : l));
    setTimeout(() => {
      setLeads(prev => prev.map(l => l.id === id ? { ...l, isProcessing: false } : l));
    }, 2500);
  };

  const handleAnalyzeAll = () => {
    setIsGlobalProcessing(true);
    setLeads(prev => prev.map(l => ({ ...l, isProcessing: true })));
    setTimeout(() => {
      setLeads(prev => prev.map(l => ({ ...l, isProcessing: false })));
      setIsGlobalProcessing(false);
    }, 3500);
  };

  // Filtragem e Ordenação Memos
  const filteredLeads = useMemo(() => {
    let filtered = leads;
    if (activeStage !== "Todos") {
      filtered = leads.filter(l => l.stage === activeStage);
    }
    return filtered.sort((a, b) => b.temperature - a.temperature);
  }, [leads, activeStage]);

  // Se o lead selecionado desaparecer da lista devido ao filtro, fecha o painel
  useEffect(() => {
    if (selectedLeadId && !filteredLeads.find(l => l.id === selectedLeadId)) {
      setSelectedLeadId(null);
    }
  }, [filteredLeads, selectedLeadId]);

  const selectedLead = leads.find(l => l.id === selectedLeadId);

  // Animação CSS helper
  const easeTransition = "transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)]";

  return (
    <div className={theme}>
      {/* App Wrapper */}
      <div className="min-h-screen bg-slate-50 dark:bg-[#0B1120] text-slate-900 dark:text-slate-50 font-sans transition-colors duration-300 overflow-x-hidden">
        
        {/* Header / Navbar */}
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
              
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center ring-2 ring-white dark:ring-[#0B1120]">
                  <User className="w-4 h-4 text-slate-600 dark:text-slate-300" />
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          
          {/* Header & Global Actions */}
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
              {isGlobalProcessing ? 'Analisando Fila...' : 'Atualizar Todos'}
            </button>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
            <div className="bg-white dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none backdrop-blur-sm">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-4">
                <span className="text-sm font-medium">Leads Ativos</span>
                <MessageCircle className="w-4 h-4" />
              </div>
              <span className="text-3xl font-semibold text-slate-900 dark:text-slate-50">{leads.length}</span>
            </div>
            
            <div className="bg-white dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none backdrop-blur-sm">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-4">
                <span className="text-sm font-medium">Prioridade Alta (Quentes)</span>
                <Flame className="w-4 h-4 text-teal-600 dark:text-teal-400" />
              </div>
              <span className="text-3xl font-semibold text-slate-900 dark:text-slate-50">
                {leads.filter(l => l.temperature >= 70).length}
              </span>
            </div>

            <div className="bg-white dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-800/60 shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-none backdrop-blur-sm">
              <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-4">
                <span className="text-sm font-medium">Etapa: Negociação</span>
                <Clock className="w-4 h-4" />
              </div>
              <span className="text-3xl font-semibold text-slate-900 dark:text-slate-50">
                {leads.filter(l => l.stage === "Em Negociação").length}
              </span>
            </div>
          </div>

          {/* DYNAMIC FLEX LAYOUT: List (Left) vs Details (Right) */}
          <div className="flex flex-col lg:flex-row items-start w-full relative">
            
            {/* LEFT COLUMN: Leads List & Funnel Tabs */}
            <div className={`${easeTransition} flex flex-col gap-4 flex-shrink-0 ${selectedLeadId ? 'w-full lg:w-[42%] lg:pr-6' : 'w-full'}`}>
              
              {/* SEGMENTED CONTROL / TABS */}
              <div className="bg-slate-200/60 dark:bg-[#131C2D] rounded-xl p-1.5 flex overflow-x-auto hide-scrollbar gap-1 border border-slate-200/50 dark:border-slate-800/50 shadow-inner">
                {FUNNEL_STAGES.map((stage) => {
                  const isActive = activeStage === stage;
                  const count = stage === "Todos" 
                    ? leads.length 
                    : leads.filter(l => l.stage === stage).length;

                  return (
                    <button
                      key={stage}
                      onClick={() => setActiveStage(stage)}
                      className={`
                        relative flex-1 min-w-[120px] flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 ease-out
                        ${isActive 
                          ? 'bg-white dark:bg-[#1E293B] text-slate-900 dark:text-slate-50 shadow-sm ring-1 ring-slate-900/5 dark:ring-white/5' 
                          : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-800/30'
                        }
                      `}
                    >
                      {stage}
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

              {/* LISTA DE LEADS */}
              <div className="flex flex-col gap-3 mt-2">
                {filteredLeads.length > 0 ? (
                  filteredLeads.map((lead) => (
                    <button
                      key={lead.id}
                      onClick={() => setSelectedLeadId(selectedLeadId === lead.id ? null : lead.id)} // Clicar novamente no mesmo fecha a aba
                      className={`text-left p-5 rounded-2xl border transition-all duration-300 transform origin-top group ${
                        selectedLeadId === lead.id 
                          ? 'bg-white dark:bg-slate-900 border-teal-500/40 dark:border-teal-500/40 shadow-md ring-1 ring-teal-500/10 dark:ring-teal-500/20' 
                          : 'bg-white/60 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800/60 hover:border-slate-300 dark:hover:border-slate-700 shadow-sm hover:shadow dark:hover:bg-slate-900/80'
                      }`}
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className={`font-semibold transition-colors ${selectedLeadId === lead.id ? 'text-teal-700 dark:text-teal-400' : 'text-slate-900 dark:text-slate-50'}`}>
                            {lead.name}
                          </h3>
                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-mono">{lead.number}</p>
                        </div>
                        {getTemperatureBadge(lead.temperature)}
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mt-2 pt-4 border-t border-slate-100 dark:border-slate-800/60">
                        <span className={`flex items-center gap-1.5 px-2 py-1 rounded-md font-medium transition-colors ${
                          selectedLeadId === lead.id ? 'bg-teal-50 dark:bg-teal-500/10 text-teal-700 dark:text-teal-400' : 'bg-slate-100 dark:bg-slate-800/50'
                        }`}>
                          <LayoutList className="w-3.5 h-3.5 opacity-70" />
                          {lead.stage}
                        </span>
                        <span className="flex items-center gap-1.5 font-medium opacity-80">
                          <Clock className="w-3.5 h-3.5" /> {lead.lastMessageAt}
                        </span>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="text-center py-16 px-4 border border-dashed border-slate-300 dark:border-slate-800 rounded-2xl bg-white/30 dark:bg-slate-900/20">
                    <LayoutList className="w-10 h-10 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
                    <p className="text-slate-500 dark:text-slate-400 font-medium">Nenhum lead nesta etapa.</p>
                  </div>
                )}
              </div>
            </div>

            {/* RIGHT COLUMN: Lead Details (Slides in and out) */}
            <div 
              className={`${easeTransition} overflow-hidden lg:pl-2 ${
                selectedLeadId 
                  ? 'w-full lg:w-[58%] opacity-100 max-h-[3000px] mt-8 lg:mt-0' 
                  : 'w-0 opacity-0 max-h-0 lg:max-h-[3000px] m-0 p-0'
              }`}
            >
              {/* Inner wrapper is essential to prevent text squishing during width transition */}
              <div className="w-full lg:w-[calc(100vw*0.58-2rem)] lg:max-w-[700px] xl:max-w-[800px] pb-8">
                {selectedLead && (
                  <div className="bg-white dark:bg-slate-900/95 rounded-2xl border border-slate-200 dark:border-slate-800/80 shadow-xl dark:shadow-[0_8px_30px_rgb(0,0,0,0.2)] overflow-hidden flex flex-col min-h-[500px]">
                    
                    {/* Lead Header */}
                    <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/50">
                      <div>
                        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-50 tracking-tight">{selectedLead.name}</h2>
                        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 font-mono">{selectedLead.number}</p>
                      </div>
                      
                      <div className="flex items-center gap-4">
                        <div className="text-right hidden sm:block">
                          <p className="text-[10px] text-slate-400 uppercase tracking-wider font-bold mb-1">Score</p>
                          {getTemperatureBadge(selectedLead.temperature)}
                        </div>
                        
                        <div className="flex items-center gap-2 border-l border-slate-200 dark:border-slate-700 pl-4">
                          <button 
                            onClick={() => handleAnalyzeSingle(selectedLead.id)}
                            disabled={selectedLead.isProcessing || isGlobalProcessing}
                            className="p-2 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800 hover:shadow-sm transition-all disabled:opacity-50 group"
                            title="Reanalisar Lead"
                          >
                            <RefreshCw className={`w-4 h-4 group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors ${selectedLead.isProcessing ? 'animate-spin text-teal-600 dark:text-teal-400' : ''}`} />
                          </button>
                          
                          {/* Close Sidebar Button */}
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

                    {/* Insights Content */}
                    <div className="p-6 md:p-8 flex-1 flex flex-col gap-8 relative">
                      
                      {/* Loading Overlay */}
                      {selectedLead.isProcessing && (
                        <div className="absolute inset-0 z-10 bg-white/70 dark:bg-[#0B1120]/60 backdrop-blur-sm flex items-center justify-center">
                          <div className="flex flex-col items-center gap-4 bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-xl border border-slate-100 dark:border-slate-700">
                            <RefreshCw className="w-8 h-8 animate-spin text-teal-600 dark:text-teal-400" />
                            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Atualizando análise pela IA...</span>
                          </div>
                        </div>
                      )}

                      {/* Resumo */}
                      <div className="space-y-3">
                        <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 flex items-center gap-2 uppercase tracking-widest">
                          <MessageCircle className="w-4 h-4" /> Resumo da Conversa
                        </h3>
                        <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed bg-slate-50 dark:bg-slate-800/30 p-5 rounded-xl border border-slate-100 dark:border-slate-800/50 shadow-sm">
                          {selectedLead.summary}
                        </p>
                      </div>

                      {/* Dica da IA */}
                      <div className="space-y-3">
                        <h3 className="text-xs font-bold text-teal-600 dark:text-teal-400 flex items-center gap-2 uppercase tracking-widest">
                          <Sparkles className="w-4 h-4" /> Dica Estratégica
                        </h3>
                        <div className="flex items-start gap-3 bg-teal-50/80 dark:bg-teal-900/20 p-5 rounded-xl border border-teal-100 dark:border-teal-500/20 shadow-sm">
                          <AlertCircle className="w-5 h-5 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
                          <p className="text-teal-900 dark:text-teal-100 text-sm leading-relaxed">
                            {selectedLead.tip}
                          </p>
                        </div>
                      </div>

                      {/* Sugestão de Resposta */}
                      <div className="space-y-3 mt-auto">
                        <h3 className="text-xs font-bold text-slate-500 dark:text-slate-400 flex items-center gap-2 uppercase tracking-widest">
                          <Send className="w-4 h-4" /> Sugestão de Resposta
                        </h3>
                        <div className="bg-slate-900 dark:bg-[#0B1120] p-5 md:p-6 rounded-xl shadow-inner relative group border border-slate-800 dark:border-slate-800/80">
                          <p className="text-slate-200 dark:text-slate-300 text-sm leading-relaxed font-medium italic">
                            "{selectedLead.suggestedReply}"
                          </p>
                        </div>
                      </div>

                    </div>

                    {/* Action Footer */}
                    <div className="p-6 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                      <button 
                        onClick={() => window.open(`https://wa.me/${selectedLead.number.replace(/\D/g, '')}?text=${encodeURIComponent(selectedLead.suggestedReply)}`, '_blank')}
                        disabled={selectedLead.isProcessing}
                        className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white dark:bg-teal-600 dark:hover:bg-teal-500 dark:text-white px-6 py-3 rounded-xl text-sm font-semibold shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-md hover:-translate-y-0.5"
                      >
                        Enviar no WhatsApp <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>

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
