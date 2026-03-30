import React from 'react';
import { LayoutDashboard, Users, MessageSquare, Database, FileText, ChevronRight, Hash } from 'lucide-react';

const Sidebar = ({ candidates }) => {
  const menuItems = [
    { icon: <LayoutDashboard size={18} />, label: 'Dashboard', active: true },
    { icon: <Users size={18} />, label: 'Candidate Pool', active: false },
    { icon: <MessageSquare size={18} />, label: 'Neural Chat', active: false },
    { icon: <Database size={18} />, label: 'Vector Store', active: false },
    { icon: <FileText size={18} />, label: 'Reports', active: false },
  ];

  return (
    <aside className="w-72 bg-slate-900 text-slate-100 flex flex-col h-full overflow-hidden">
      {/* Brand Header */}
      <div className="p-8 pb-4 flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-indigo-700 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <span className="font-bold text-xl leading-none">TQ</span>
        </div>
        <div className="flex flex-col">
          <span className="font-bold text-lg tracking-tight">TalentIQ</span>
          <span className="text-[10px] text-indigo-400 font-bold tracking-[0.2em] uppercase">Enterprise Agent</span>
        </div>
      </div>

      <nav className="flex-1 px-4 py-8 flex flex-col gap-1 overflow-y-auto chat-scrollbar">
        <p className="px-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Main Console</p>
        
        {menuItems.map((item, idx) => (
          <button 
            key={idx}
            className={`w-full flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-200 group ${
              item.active 
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/50' 
              : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <span className={`${item.active ? 'text-white' : 'text-slate-500 group-hover:text-indigo-400'}`}>
              {item.icon}
            </span>
            <span className="font-semibold text-sm">{item.label}</span>
          </button>
        ))}

        {/* ── ADVANCED FEATURE: TOP CANDIDATES SECTION ── */}
        <div className="mt-12">
          <p className="px-4 text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Recognized Talent</p>
          <div className="flex flex-col gap-2">
            {candidates.length > 0 ? (
              candidates.map((name, idx) => (
                <div 
                  key={idx} 
                  className="mx-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg flex items-center justify-between group cursor-pointer hover:bg-slate-800 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]"></div>
                    <span className="text-xs font-medium text-slate-300 group-hover:text-white truncate max-w-[120px] tracking-tight">{name}</span>
                  </div>
                  <ChevronRight size={12} className="text-slate-600 group-hover:text-indigo-400 transition-colors" />
                </div>
              ))
            ) : (
              <div className="mx-2 px-4 py-8 border border-dashed border-slate-800 rounded-xl text-center">
                <span className="text-[10px] text-slate-600 font-semibold uppercase italic">Gathering Intelligence...</span>
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* Profile / Bottom Area */}
      <div className="p-6 border-t border-slate-800 mt-auto bg-slate-950/20 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-slate-700 border-2 border-indigo-500/30 flex items-center justify-center font-bold text-xs text-indigo-100">
            HR
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold text-white leading-none mb-1">Lead Recruiter</span>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">Enterprise Plan</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
