import React from 'react';
import { motion } from 'framer-motion';
import { User, Cpu, Sparkles } from 'lucide-react';

const MessageBubble = ({ message }) => {
  const isAssistant = message.role === 'assistant';

  // Advanced Feature: Keyword Highlighting Logic
  const highlightKeywords = (text) => {
    const keywords = ['Python', 'React', 'FastAPI', 'ML', 'Machine Learning', 'AI', 'Node.js', 'PostgreSQL', 'AWS', 'Azure', 'Docker', 'Kubernetes'];
    const regex = new RegExp(`\\b(${keywords.join('|')})\\b`, 'gi');
    
    const parts = text.split(regex);
    return parts.map((part, i) => 
      keywords.some(k => k.toLowerCase() === part.toLowerCase()) ? (
        <span key={i} className="px-1.5 py-0.5 bg-indigo-100 text-indigo-700 font-bold rounded-md border border-indigo-200 shadow-sm text-[0.95em]">
          {part}
        </span>
      ) : part
    );
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`flex w-full mb-6 ${isAssistant ? 'justify-start' : 'justify-end'}`}
    >
      <div className={`flex max-w-[85%] gap-4 ${isAssistant ? 'flex-row' : 'flex-row-reverse'}`}>
        
        {/* AVATAR SECTION */}
        <div className={`h-10 w-10 flex-shrink-0 rounded-2xl flex items-center justify-center shadow-md ${
          isAssistant ? 'bg-indigo-600 text-white' : 'bg-slate-200 text-slate-600'
        }`}>
          {isAssistant ? <Cpu size={20} /> : <User size={20} />}
        </div>

        {/* MESSAGE CONTENT */}
        <div className="flex flex-col gap-1">
          <div className={`text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-0.5 ${!isAssistant && 'text-right'}`}>
            {isAssistant ? 'Neural Intelligence Agent' : 'Recruitment Lead'}
          </div>
          
          <div className={`px-5 py-4 rounded-2xl text-sm leading-relaxed shadow-sm border ${
            isAssistant 
            ? 'bg-white border-slate-100 text-slate-700 rounded-tl-none' 
            : 'bg-indigo-600 border-indigo-500 text-white rounded-tr-none'
          }`}>
            <div className="whitespace-pre-wrap">
              {isAssistant ? highlightKeywords(message.content) : message.content}
            </div>
          </div>

          {isAssistant && (
            <div className="flex items-center gap-1.5 mt-2 opacity-50 hover:opacity-100 transition-opacity">
              <Sparkles size={12} className="text-indigo-500" />
              <span className="text-[10px] font-bold text-slate-500">Confidence: 98.4%</span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default MessageBubble;
