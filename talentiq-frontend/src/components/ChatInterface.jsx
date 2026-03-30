import React, { useRef, useEffect, useState } from 'react';
import MessageBubble from './MessageBubble';
import { Send, Trash2, ShieldCheck, Loader2, Sparkles } from 'lucide-react';
import { askQuestion } from '../api/client';
import { motion, AnimatePresence } from 'framer-motion';

const ChatInterface = ({ messages, setMessages }) => {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { id: Date.now(), role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const data = await askQuestion(input);
      const assistantMessage = { id: Date.now() + 1, role: 'assistant', content: data.answer };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = { id: Date.now() + 2, role: 'assistant', content: `❌ Error: ${err.message}` };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([{ 
      id: 1, 
      role: 'assistant', 
      content: 'Memory cleared. Intelligence engine ready for new session.' 
    }]);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50/50 relative">
      
      {/* ── MESSAGES LIST ── */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-8 py-10 chat-scrollbar flex flex-col gap-2"
      >
        <AnimatePresence>
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
        </AnimatePresence>

        {/* TYPING INDICATOR */}
        {isLoading && (
          <motion.div 
            initial={{ opacity: 0, y: 5 }} 
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-4"
          >
            <div className="h-10 w-10 rounded-2xl bg-indigo-600 text-white flex items-center justify-center shadow-lg">
              <Loader2 size={18} className="animate-spin" />
            </div>
            <div className="px-5 py-4 bg-white border border-slate-100 rounded-2xl rounded-tl-none shadow-sm flex items-center gap-2">
              <div className="dot h-1.5 w-1.5 bg-indigo-400 rounded-full"></div>
              <div className="dot h-1.5 w-1.5 bg-indigo-400 rounded-full"></div>
              <div className="dot h-1.5 w-1.5 bg-indigo-400 rounded-full"></div>
            </div>
          </motion.div>
        )}
      </div>

      {/* ── INPUT AREA ── */}
      <div className="p-8 pt-0 bg-transparent">
        <form 
          onSubmit={handleSend}
          className="relative max-w-4xl mx-auto group"
        >
          <div className="absolute -top-3 left-4 px-3 py-1 bg-white border border-slate-100 rounded-lg shadow-sm flex items-center gap-2 transition-all group-focus-within:-translate-y-1">
            <Sparkles size={12} className="text-indigo-600" />
            <span className="text-[10px] font-bold text-slate-500 uppercase">Contextual Intelligence Active</span>
          </div>

          <div className="flex items-center gap-3 bg-white p-2 pl-6 rounded-2xl shadow-xl shadow-indigo-900/5 border border-slate-100 ring-4 ring-slate-50 transition-all focus-within:ring-indigo-50 focus-within:border-indigo-100">
            <textarea
              rows="1"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend(e);
                }
              }}
              placeholder="Query our talent pool or analyze specific candidates..."
              className="flex-1 bg-transparent py-3 text-sm text-slate-700 placeholder:text-slate-400 outline-none resize-none"
            />
            
            <button 
              type="button"
              onClick={clearChat}
              className="p-3 text-slate-300 hover:text-rose-500 rounded-xl transition-all"
              title="Clear Session"
            >
              <Trash2 size={20} />
            </button>

            <button 
              type="submit"
              disabled={isLoading || !input.trim()}
              className={`p-3 rounded-xl transition-all flex items-center gap-2 ${
                input.trim() 
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30' 
                : 'bg-slate-100 text-slate-300'
              }`}
            >
              <Send size={20} />
              <span className="font-bold text-xs pr-1">ANALYZE</span>
            </button>
          </div>
          
          <div className="mt-4 flex items-center justify-center gap-6 opacity-40">
            <div className="flex items-center gap-1.5">
              <ShieldCheck size={12} className="text-slate-500" />
              <span className="text-[10px] font-medium text-slate-500 uppercase tracking-tighter">Enterprise Encryption Active</span>
            </div>
            <div className="h-1 w-1 bg-slate-300 rounded-full"></div>
            <span className="text-[10px] font-medium text-slate-500 uppercase tracking-tighter">Proprietary TalentIQ v2.1</span>
          </div>
        </form>
      </div>

    </div>
  );
};

export default ChatInterface;
