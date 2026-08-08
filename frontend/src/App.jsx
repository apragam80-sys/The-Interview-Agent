import React, { useState } from 'react';
import { Bot, RotateCcw, AlertCircle } from 'lucide-react';
import CandidateSelector from './components/CandidateSelector';
import ChatInterface from './components/ChatInterface';
import ProgressTracker from './components/ProgressTracker';
import FeedbackDashboard from './components/FeedbackDashboard';
import { startInterviewSession, sendCandidateAnswer } from './services/api';

/**
 * Main Application Container Component.
 */
export default function App() {
  const [view, setView] = useState('SELECTOR'); // 'SELECTOR' | 'INTERVIEW' | 'FEEDBACK'
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [sessionId, setSessionId] = useState('');
  const [messages, setMessages] = useState([]);
  const [turnCount, setTurnCount] = useState(0);
  const [coveredDays, setCoveredDays] = useState([]);
  const [isFollowUp, setIsFollowUp] = useState(false);
  const [latestScore, setLatestScore] = useState(null);
  const [averageScore, setAverageScore] = useState(null);
  const [difficultyLevel, setDifficultyLevel] = useState('MID');
  const [feedback, setFeedback] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const generateSessionId = (candId) => {
    return `session-${candId || 'candidate'}-${Date.now().toString(36)}`;
  };

  // Turn 1: Start interview with selected candidate
  const handleStartInterview = async (candidate) => {
    setError(null);
    setIsLoading(true);
    const newSessionId = generateSessionId(candidate?.member?.id);

    setSelectedCandidate(candidate);
    setSessionId(newSessionId);
    setMessages([]);
    setTurnCount(0);
    setCoveredDays([]);
    setLatestScore(null);
    setAverageScore(null);
    setFeedback(null);

    try {
      const response = await startInterviewSession(newSessionId, candidate);
      setMessages([{
        role: 'assistant',
        content: response.reply,
        isFollowUp: response.isFollowUp || false
      }]);
      setTurnCount(response.totalQuestions || 1);
      setCoveredDays(response.coveredDays || [7]);
      setIsFollowUp(response.isFollowUp || false);
      if (response.score !== undefined) setLatestScore(response.score);
      if (response.averageScore !== undefined) setAverageScore(response.averageScore);
      
      const signals = candidate?.signals || {};
      const firstTry = signals.missionsFirstTry || 0;
      const comp = signals.missionsCompleted || 0;
      const tier = firstTry >= 20 ? 'SENIOR' : comp >= 15 ? 'MID' : 'JUNIOR';
      setDifficultyLevel(tier);

      setView('INTERVIEW');
    } catch (err) {
      setError(err.message || 'Failed to initialize session');
    } finally {
      setIsLoading(false);
    }
  };

  // Turn N: Progress conversation turn with candidate answer
  const handleSendMessage = async (userAnswer) => {
    if (!sessionId || isLoading) return;

    setError(null);
    setIsLoading(true);

    const tempUserMsg = { role: 'user', content: userAnswer };
    const currentMessages = [...messages, tempUserMsg];
    setMessages(currentMessages);

    try {
      const response = await sendCandidateAnswer(sessionId, userAnswer);

      // Annotate user's response with score
      const scoredUserMsg = {
        role: 'user',
        content: userAnswer,
        score: response.score !== undefined ? response.score : null
      };

      const assistantMsg = {
        role: 'assistant',
        content: response.reply,
        isFollowUp: response.isFollowUp || false
      };

      setMessages([...messages, scoredUserMsg, assistantMsg]);

      if (response.totalQuestions !== undefined) setTurnCount(response.totalQuestions);
      else setTurnCount((prev) => prev + 1);

      if (response.coveredDays) setCoveredDays(response.coveredDays);
      if (response.score !== undefined && response.score !== null) setLatestScore(response.score);
      if (response.averageScore !== undefined && response.averageScore !== null) setAverageScore(response.averageScore);
      setIsFollowUp(Boolean(response.isFollowUp));

      if (response.done && response.feedback) {
        setFeedback(response.feedback);
        setView('FEEDBACK');
      }
    } catch (err) {
      setError(err.message || 'Failed to progress interview turn');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetInterview = () => {
    setView('SELECTOR');
    setSelectedCandidate(null);
    setSessionId('');
    setMessages([]);
    setTurnCount(0);
    setCoveredDays([]);
    setLatestScore(null);
    setAverageScore(null);
    setIsFollowUp(false);
    setFeedback(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Header */}
      <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-base text-white tracking-tight">Adaptive AI Interview Agent</span>
              <span className="hidden sm:inline-block ml-2 text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Multi-Agent Architecture
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {view !== 'SELECTOR' && (
              <button
                onClick={handleResetInterview}
                className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-300 flex items-center gap-1.5 transition-all"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Change Candidate</span>
              </button>
            )}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/90 border border-slate-800 text-xs text-slate-300 font-mono shadow-inner">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>POST /api/interview</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center justify-between shadow-lg">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-xs underline hover:text-white">Dismiss</button>
          </div>
        )}

        {view === 'SELECTOR' && (
          <CandidateSelector onSelectCandidate={handleStartInterview} isLoading={isLoading} />
        )}

        {view === 'INTERVIEW' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <ChatInterface
                messages={messages}
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
                isComplete={view === 'FEEDBACK'}
              />
            </div>
            <div>
              <ProgressTracker
                turnCount={turnCount}
                coveredDays={coveredDays}
                candidate={selectedCandidate}
                sessionId={sessionId}
                isFollowUp={isFollowUp}
                latestScore={latestScore}
                averageScore={averageScore}
                difficultyLevel={difficultyLevel}
              />
            </div>
          </div>
        )}

        {view === 'FEEDBACK' && (
          <FeedbackDashboard
            feedback={feedback}
            candidate={selectedCandidate}
            onResetInterview={handleResetInterview}
            sessionId={sessionId}
          />
        )}
      </main>
    </div>
  );
}
