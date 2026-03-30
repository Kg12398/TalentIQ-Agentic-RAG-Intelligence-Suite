import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import { LayoutDashboard, Users, MessageSquare, Settings, Zap } from 'lucide-react';

const App = () => {
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      role: 'assistant', 
      content: 'Welcome back to **TalentIQ Intelligence Suite**. How can I help you analyze your candidate pool today?' 
    }
  ]);
  const [topCandidates, setTopCandidates] = useState([]);

  // Extract names from responses to populate the "Top Candidates" section (Advanced Feature)
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage?.role === 'assistant') {
      // Simple regex for common Indian/Western names or capitalized words in bullet points
      const namesFound = lastMessage.content.match(/(?:\d\.\s|\*\s)([A-Z][a-z]+\s[A-Z][a-z]+)/g);
      if (namesFound) {
        const cleanedNames = namesFound.map(n => n.replace(/^\d\.\s|\*\s/, ''));
        setTopCandidates(prev => [...new Set([...prev, ...cleanedNames])].slice(0, 5));
      }
    }
  }, [messages]);

  return (
    <div className="flex h-screen bg-slate-50 font-sans">
      {/* ── LEFT NAVIGATION SIDEBAR ── */}
      <Sidebar candidates={topCandidates} />

      {/* ── MAIN APP AREA ── */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-white shadow-2xl rounded-l-3xl border-l border-slate-200">
        
        {/* Header Branding */}
        <header className="px-8 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-lg text-white">
              <Zap size={20} fill="currentColor" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-800 leading-tight">Orchestrator Llama-3.3</h1>
              <p className="text-xs text-slate-400 font-medium tracking-wide uppercase">Real-time Intelligence Engine</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="px-3 py-1 bg-emerald-50 text-emerald-600 rounded-full text-xs font-bold border border-emerald-100">
              ● API ACTIVE
            </div>
            <button className="text-slate-400 hover:text-slate-600 transition-colors">
              <Settings size={20} />
            </button>
          </div>
        </header>

        {/* ── CHAT ENGINE ── */}
        <ChatInterface 
          messages={messages} 
          setMessages={setMessages} 
        />
        
      </main>
    </div>
  );
};

export default App;
