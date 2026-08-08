import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Zap, Award } from 'lucide-react';

/**
 * ChatInterface Component.
 * 
 * Props:
 * @param {Array<{role: string, content: string, isFollowUp?: boolean, score?: number}>} messages - Conversation history list
 * @param {Function} onSendMessage - Callback when user submits answer: (messageText) => void
 * @param {boolean} isLoading - Turn execution loading state
 * @param {boolean} isComplete - True if interview is completed
 */
export default function ChatInterface({
  messages = [],
  onSendMessage,
  isLoading = false,
  isComplete = false,
}) {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading || isComplete) return;
    onSendMessage(inputMessage.trim());
    setInputMessage('');
  };

  const getScoreBadgeClass = (score) => {
    if (score < 0) return 'bg-rose-950/80 text-rose-300 border-rose-500 shadow-rose-950/30';
    if (score >= 75) return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    if (score >= 50) return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
    return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
  };

  return (
    <div className="glass-panel rounded-2xl border border-slate-800 flex flex-col h-[650px] overflow-hidden shadow-2xl">
      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.map((msg, index) => {
          const isBot = msg.role === 'assistant';
          const isProbe = msg.isFollowUp;

          return (
            <div
              key={index}
              className={`flex gap-3 ${isBot ? 'justify-start' : 'justify-end'}`}
            >
              {isBot && (
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                  isProbe 
                    ? 'bg-amber-500/20 border border-amber-500/40 text-amber-400' 
                    : 'bg-blue-600/20 border border-blue-500/40 text-blue-400'
                }`}>
                  {isProbe ? <Zap className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
              )}

              <div
                className={`max-w-[82%] rounded-2xl p-4 text-sm leading-relaxed ${
                  isBot
                    ? isProbe 
                      ? 'bg-slate-900/90 border border-amber-500/30 text-slate-100'
                      : 'bg-slate-900 border border-slate-800 text-slate-100'
                    : 'bg-blue-600 text-white font-normal'
                }`}
              >
                {/* Assistant Badge */}
                {isBot && (
                  <div className="flex items-center justify-between gap-1.5 mb-1.5 text-xs font-semibold">
                    <span className={`flex items-center gap-1.5 ${isProbe ? 'text-amber-400' : 'text-blue-400'}`}>
                      {isProbe ? <Zap className="w-3 h-3" /> : <Sparkles className="w-3 h-3" />}
                      {isProbe ? 'Adaptive Deep-Dive Probe' : 'Interviewer Agent'}
                    </span>
                  </div>
                )}

                {/* Candidate Score Badge */}
                {!isBot && msg.score !== undefined && msg.score !== null && (
                  <div className="flex flex-col items-end mb-2">
                    <span className={`text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full border flex items-center gap-1 ${getScoreBadgeClass(msg.score)}`}>
                      <Award className="w-3 h-3" />
                      {msg.score < 0 ? '⚠️ Professionalism penalty: -25 pts' : `Technical Score: ${msg.score}/100`}
                    </span>
                    {msg.score < 0 && (
                      <span className="text-[9px] text-rose-200/90 font-medium mt-0.5">
                        Applied to Behavior & Communication score
                      </span>
                    )}
                  </div>
                )}

                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>

              {!isBot && (
                <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 shrink-0">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          );
        })}

        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 shrink-0 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 text-sm text-slate-400 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
              <span>Multi-agent evaluator scoring answer and planning next turn...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-4 bg-slate-950 border-t border-slate-800">
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder={isComplete ? "Interview finished." : "Type your technical response..."}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={isLoading || isComplete}
            className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
          <button
            type="submit"
            disabled={isLoading || !inputMessage.trim() || isComplete}
            className="h-10 px-5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold text-xs flex items-center justify-center gap-1.5 transition-all disabled:opacity-50"
          >
            <span>Send</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>
    </div>
  );
}
