import React from 'react';
import { Target, Calendar, Award, Zap, Sparkles, TrendingUp, AlertTriangle } from 'lucide-react';

/**
 * ProgressTracker Component.
 * 
 * Displays live candidate evaluation metrics:
 * - Real-time score & running average
 * - Question depth (8 max cap) & curriculum coverage (>=4 days)
 * - Adaptive probing status
 * - Negative score penalty alerts
 * - Tested curriculum day badges
 */
export default function ProgressTracker({
  turnCount = 0,
  coveredDays = [],
  candidate = null,
  sessionId = '',
  isFollowUp = false,
  latestScore = null,
  averageScore = null,
  difficultyLevel = 'MID',
}) {
  const minQuestions = 8;
  const minDays = 4;

  const uniqueDays = Array.from(new Set(coveredDays));
  const questionsProgress = Math.min(100, Math.round((Math.min(turnCount, minQuestions) / minQuestions) * 100));
  const daysProgress = Math.min(100, Math.round((uniqueDays.length / minDays) * 100));

  const member = candidate?.member || {};

  const getScoreColor = (score) => {
    if (score === null || score === undefined) return 'text-slate-400 border-slate-700 bg-slate-800/40';
    if (score < 0) return 'text-rose-400 border-rose-500/60 bg-rose-950/40 shadow-rose-950/20';
    if (score >= 75) return 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10';
    if (score >= 50) return 'text-amber-400 border-amber-500/40 bg-amber-500/10';
    return 'text-rose-400 border-rose-500/40 bg-rose-500/10';
  };

  const getScoreBarColor = (score) => {
    if (score === null || score === undefined) return 'bg-slate-700';
    if (score < 0) return 'bg-rose-600';
    if (score >= 75) return 'bg-emerald-500';
    if (score >= 50) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-5 shadow-xl">
      {/* Candidate Header */}
      <div className="flex items-start justify-between border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            {member.name || 'Candidate'}
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
              {difficultyLevel}
            </span>
          </h2>
          <p className="text-xs text-slate-400">{member.jobRole || 'Software Engineer'}</p>
        </div>
        <div className="text-right">
          <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Session ID</div>
          <div className="text-xs font-mono text-slate-300 truncate max-w-[90px]" title={sessionId}>
            {sessionId || 'N/A'}
          </div>
        </div>
      </div>

      {/* Live Evaluation Score Cards */}
      <div className="grid grid-cols-2 gap-3">
        {/* Latest Answer Score */}
        <div className={`p-3 rounded-xl border ${getScoreColor(latestScore)} flex flex-col justify-between transition-all relative overflow-hidden`}>
          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300 mb-1">
            <span className="flex items-center gap-1">
              <Award className="w-3.5 h-3.5" />
              Latest Tech Score
            </span>
          </div>
          <div className="text-2xl font-black font-mono">
            {latestScore !== null && latestScore !== undefined ? (
              <>
                <span className={latestScore < 0 ? 'text-rose-400' : ''}>
                  {latestScore < 0 ? '-25' : latestScore}
                </span>
                <span className="text-xs font-normal text-slate-400 font-sans ml-1">/100</span>
              </>
            ) : (
              '--'
            )}
          </div>
          {latestScore !== null && latestScore < 0 && (
            <div className="text-[10px] text-rose-300 bg-rose-950/80 border border-rose-500/40 px-1.5 py-0.5 rounded font-semibold flex items-center gap-1 mt-1 leading-tight">
              <AlertTriangle className="w-3 h-3 text-rose-400 shrink-0" />
              <span>Professionalism penalty applied to Behavior</span>
            </div>
          )}
          <div className="w-full h-1.5 bg-slate-800 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full ${getScoreBarColor(latestScore)} transition-all duration-500`}
              style={{ width: `${Math.max(0, latestScore ?? 0)}%` }}
            />
          </div>
        </div>

        {/* Average Score */}
        <div className={`p-3 rounded-xl border ${getScoreColor(averageScore)} flex flex-col justify-between transition-all`}>
          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-300 mb-1">
            <span className="flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5" />
              Avg Tech Score
            </span>
          </div>
          <div className="text-2xl font-black font-mono">
            {averageScore !== null && averageScore !== undefined ? (
              <>
                <span className={averageScore < 0 ? 'text-rose-400' : ''}>{averageScore}</span>
                <span className="text-xs font-normal text-slate-400 font-sans ml-1">/100</span>
              </>
            ) : (
              '--'
            )}
          </div>
          <div className="w-full h-1.5 bg-slate-800 rounded-full mt-2 overflow-hidden">
            <div
              className={`h-full ${getScoreBarColor(averageScore)} transition-all duration-500`}
              style={{ width: `${Math.max(0, averageScore ?? 0)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Adaptive Mode Indicator */}
      {isFollowUp ? (
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs animate-pulse">
          <Zap className="w-4 h-4 text-amber-400 shrink-0" />
          <div className="font-medium leading-tight">
            Adaptive Follow-up Probe active (testing architectural depth)
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs">
          <Sparkles className="w-4 h-4 text-blue-400 shrink-0" />
          <div className="font-medium leading-tight">
            Curriculum Roadmap Progression
          </div>
        </div>
      )}

      {/* Questions Depth Metric (Min 8) */}
      <div>
        <div className="flex items-center justify-between text-xs mb-1.5">
          <span className="text-slate-300 font-semibold flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5 text-blue-400" />
            Interview Depth (Min 8)
          </span>
          <span className="font-mono text-xs font-bold text-blue-400">
            {Math.min(minQuestions, turnCount)} / {minQuestions}
          </span>
        </div>
        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${questionsProgress}%` }}
          />
        </div>
      </div>

      {/* Curriculum Days Metric (Min 4) */}
      <div>
        <div className="flex items-center justify-between text-xs mb-1.5">
          <span className="text-slate-300 font-semibold flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-emerald-400" />
            Curriculum Coverage (Min 4)
          </span>
          <span className="font-mono text-xs font-bold text-emerald-400">
            {Math.min(minDays, uniqueDays.length)} / {minDays}
          </span>
        </div>
        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-500 transition-all duration-300"
            style={{ width: `${daysProgress}%` }}
          />
        </div>
      </div>

      {/* Days Badges */}
      {uniqueDays.length > 0 && (
        <div className="pt-2 border-t border-slate-800">
          <div className="text-[11px] text-slate-400 font-semibold mb-2">Tested Days ({uniqueDays.length})</div>
          <div className="flex flex-wrap gap-1.5">
            {uniqueDays.map((day) => (
              <span
                key={day}
                className="text-[11px] font-mono px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 text-slate-200 shadow-sm"
              >
                Day {day}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
