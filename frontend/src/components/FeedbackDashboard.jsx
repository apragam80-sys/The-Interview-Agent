import React from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  ArrowRightCircle, 
  RotateCcw, 
  Sparkles, 
  MessageSquare, 
  Award, 
  ShieldCheck, 
  BrainCircuit, 
  Layers, 
  Gauge, 
  UserCheck, 
  Target, 
  Eye 
} from 'lucide-react';

/**
 * FeedbackDashboard Component.
 * 
 * Displays the comprehensive technical and behavioral interview evaluation report.
 * 
 * Props:
 * @param {Object} feedback - Structured feedback payload matching FeedbackData schema
 * @param {Object} candidate - Candidate profile object
 * @param {Function} onResetInterview - Callback to restart interview
 * @param {string} sessionId - Interview session ID
 */
export default function FeedbackDashboard({
  feedback = null,
  candidate = null,
  onResetInterview,
  sessionId = '',
}) {
  if (!feedback) {
    return (
      <div className="glass-panel p-8 rounded-2xl border border-slate-800 text-center">
        <p className="text-slate-400">No feedback report available.</p>
      </div>
    );
  }

  const { 
    summary = '', 
    strengths = [], 
    gaps = [], 
    next = [],
    behavior = null,
    technical_score = 75,
    communication_score = 75,
    overall_score = null
  } = feedback;

  const member = candidate?.member || {};
  
  // Calculate blended overall score if not explicitly returned
  const finalOverallScore = overall_score !== null && overall_score !== undefined
    ? overall_score
    : Math.round(0.70 * technical_score + 0.30 * communication_score);

  // Behavioral dimension definitions for rendering
  const behaviorDimensions = behavior ? [
    {
      key: 'communication_clarity',
      label: 'Communication Clarity',
      icon: MessageSquare,
      data: behavior.communication_clarity,
      color: 'blue'
    },
    {
      key: 'technical_communication',
      label: 'Technical Communication',
      icon: BrainCircuit,
      data: behavior.technical_communication,
      color: 'emerald'
    },
    {
      key: 'confidence',
      label: 'Confidence',
      icon: Gauge,
      data: behavior.confidence,
      color: 'purple'
    },
    {
      key: 'conciseness',
      label: 'Conciseness',
      icon: Target,
      data: behavior.conciseness,
      color: 'cyan'
    },
    {
      key: 'professionalism',
      label: 'Professionalism',
      icon: ShieldCheck,
      data: behavior.professionalism,
      color: 'emerald'
    },
    {
      key: 'answer_structure',
      label: 'Answer Structure',
      icon: Layers,
      data: behavior.answer_structure,
      color: 'amber'
    },
    {
      key: 'responsiveness',
      label: 'Responsiveness',
      icon: UserCheck,
      data: behavior.responsiveness,
      color: 'indigo'
    }
  ] : [];

  const presenceData = behavior?.overall_interview_presence || { score: 7.5, assessment: '' };
  const presenceSummary = behavior?.overall_presence_summary || '';
  const communicationStyles = behavior?.communication_styles || ['Clear & Structured'];
  const languageObservations = behavior?.language_observations || [];

  return (
    <div className="space-y-6 pb-12">
      {/* Overview & Score Banner Card */}
      <div className="glass-panel p-6 md:p-8 rounded-2xl border border-blue-500/30 shadow-2xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold mb-2">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Interview Evaluation Report
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              {member.name || 'Candidate'}
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              {member.jobRole} • Session ID: <span className="font-mono text-slate-300">{sessionId}</span>
            </p>
          </div>

          <button
            onClick={onResetInterview}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white flex items-center gap-2 transition-all shadow-lg shadow-blue-500/20 hover:scale-105 w-fit"
          >
            <RotateCcw className="w-4 h-4" />
            <span>New Interview</span>
          </button>
        </div>

        {/* Top-Level Composite Score Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Overall Blended Score */}
          <div className="bg-gradient-to-br from-blue-950/60 to-slate-900/90 border border-blue-500/40 p-5 rounded-xl relative overflow-hidden flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-blue-300 uppercase tracking-wider flex items-center gap-1.5">
                <Award className="w-4 h-4 text-blue-400" />
                Overall Interview Score
              </span>
              <span className="text-[10px] text-blue-400 bg-blue-500/20 px-2 py-0.5 rounded-md font-mono">
                70% Tech / 30% Comm
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className={`text-4xl font-extrabold tracking-tight ${
                finalOverallScore >= 80 ? 'text-emerald-400' :
                finalOverallScore >= 60 ? 'text-blue-400' :
                finalOverallScore >= 40 ? 'text-amber-400' : 'text-rose-400'
              }`}>
                {finalOverallScore}
              </span>
              <span className="text-sm font-medium text-slate-400">/ 100</span>
            </div>
            <div className="w-full bg-slate-800/80 rounded-full h-1.5 mt-3 overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-700 ${
                  finalOverallScore >= 80 ? 'bg-emerald-500' :
                  finalOverallScore >= 60 ? 'bg-blue-500' :
                  finalOverallScore >= 40 ? 'bg-amber-500' : 'bg-rose-500'
                }`}
                style={{ width: `${Math.max(5, Math.min(100, finalOverallScore))}%` }}
              />
            </div>
          </div>

          {/* Technical Performance Score */}
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-xl flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <BrainCircuit className="w-4 h-4 text-emerald-400" />
                Technical Performance
              </span>
              <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md font-mono">
                Weight: 70%
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className={`text-3xl font-extrabold ${
                technical_score >= 80 ? 'text-emerald-400' :
                technical_score >= 60 ? 'text-emerald-300' :
                technical_score >= 40 ? 'text-amber-400' : 'text-rose-400'
              }`}>
                {technical_score}
              </span>
              <span className="text-sm font-medium text-slate-400">/ 100</span>
            </div>
            <div className="text-[10px] text-emerald-400/80 font-medium mt-1">
              Pure technical knowledge (uncontaminated)
            </div>
            <div className="w-full bg-slate-800/80 rounded-full h-1.5 mt-2 overflow-hidden">
              <div 
                className="h-full bg-emerald-500 rounded-full transition-all duration-700"
                style={{ width: `${Math.max(5, Math.min(100, technical_score))}%` }}
              />
            </div>
          </div>

          {/* Interview Communication Score */}
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-xl flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <MessageSquare className="w-4 h-4 text-purple-400" />
                Communication & Behavior
              </span>
              <span className="text-[10px] text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded-md font-mono">
                Weight: 30%
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className={`text-3xl font-extrabold ${
                communication_score >= 80 ? 'text-purple-400' :
                communication_score >= 60 ? 'text-purple-300' :
                communication_score >= 40 ? 'text-amber-400' : 'text-rose-400'
              }`}>
                {communication_score}
              </span>
              <span className="text-sm font-medium text-slate-400">/ 100</span>
            </div>
            {behavior?.professionalism?.score < 5.0 && (
              <div className="text-[10px] text-rose-300 bg-rose-950/80 border border-rose-500/40 px-1.5 py-0.5 rounded font-semibold flex items-center gap-1 mt-1 leading-tight">
                <AlertTriangle className="w-3 h-3 text-rose-400 shrink-0" />
                <span>⚠️ Professionalism penalty applied (-25 pts)</span>
              </div>
            )}
            <div className="w-full bg-slate-800/80 rounded-full h-1.5 mt-2 overflow-hidden">
              <div 
                className="h-full bg-purple-500 rounded-full transition-all duration-700"
                style={{ width: `${Math.max(5, Math.min(100, communication_score))}%` }}
              />
            </div>
          </div>
        </div>

        {/* Executive Summary */}
        <div className="pt-2">
          <h2 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            Executive Summary
          </h2>
          <p className="text-sm text-slate-200 bg-slate-900/90 p-4 rounded-xl border border-slate-800 leading-relaxed">
            {summary}
          </p>
        </div>
      </div>

      {/* =================================================================== */}
      {/* NEW SECTION: Interview Behavior & Communication                     */}
      {/* =================================================================== */}
      {behavior && (
        <div className="glass-panel p-6 md:p-8 rounded-2xl border border-purple-500/20 shadow-xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-400">
                <MessageSquare className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Interview Behavior & Communication</h2>
                <p className="text-xs text-slate-400">Evidence-based analysis of conversation clarity, terminology, structure, and responsiveness.</p>
              </div>
            </div>

            {/* Overall Interview Presence Badge */}
            <div className="bg-purple-950/40 border border-purple-500/30 px-4 py-2 rounded-xl flex items-center gap-3 self-start sm:self-auto">
              <Eye className="w-4 h-4 text-purple-400" />
              <div>
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Overall Interview Presence</div>
                <div className="text-sm font-extrabold text-purple-300">
                  {presenceData.score?.toFixed ? presenceData.score.toFixed(1) : presenceData.score} / 10
                </div>
              </div>
            </div>
          </div>

          {/* Holistic Presence Summary */}
          {presenceSummary && (
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 text-xs text-slate-300 leading-relaxed italic">
              "{presenceSummary}"
            </div>
          )}

          {/* Behavioral Dimensions Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {behaviorDimensions.map((dim) => {
              const IconComponent = dim.icon;
              const dimScore = dim.data?.score ?? 7.0;
              const dimAssessment = dim.data?.assessment || 'Consistent performance observed.';

              return (
                <div 
                  key={dim.key}
                  className="bg-slate-900/70 p-4 rounded-xl border border-slate-800/90 hover:border-slate-700 transition-all flex flex-col justify-between gap-3"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-white flex items-center gap-2">
                      <IconComponent className="w-4 h-4 text-slate-400" />
                      {dim.label}
                    </span>
                    <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded-md ${
                      dimScore >= 8.0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
                      dimScore >= 6.0 ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30' :
                      dimScore >= 4.0 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' :
                      'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                    }`}>
                      {dimScore.toFixed ? dimScore.toFixed(1) : dimScore} / 10
                    </span>
                  </div>

                  {/* Dimension score bar */}
                  <div className="w-full bg-slate-800 rounded-full h-1 overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${
                        dimScore >= 8.0 ? 'bg-emerald-400' :
                        dimScore >= 6.0 ? 'bg-blue-400' :
                        dimScore >= 4.0 ? 'bg-amber-400' : 'bg-rose-400'
                      }`}
                      style={{ width: `${Math.max(5, Math.min(100, dimScore * 10))}%` }}
                    />
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    {dimAssessment}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Communication Style Badges & Language Observations */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2">
            {/* Communication Style Badges */}
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 space-y-3">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-purple-400" />
                Communication Style
              </h3>
              <div className="flex flex-wrap gap-2">
                {communicationStyles.map((style, idx) => (
                  <span 
                    key={idx}
                    className="px-3 py-1 rounded-lg text-xs font-semibold bg-purple-500/10 border border-purple-500/30 text-purple-300"
                  >
                    {style}
                  </span>
                ))}
              </div>
            </div>

            {/* Language Observations */}
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 space-y-3">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                Language Observations
              </h3>
              <ul className="space-y-1.5">
                {languageObservations.map((obs, idx) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">•</span>
                    <span>{obs}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* Existing Strengths, Gaps, Next Grid                                */}
      {/* =================================================================== */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Strengths */}
        <div className="glass-panel p-5 rounded-2xl border border-emerald-500/20 shadow-lg">
          <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Strengths ({strengths.length})
          </h3>
          <ul className="space-y-2">
            {strengths.map((item, idx) => (
              <li key={idx} className="text-xs text-slate-200 bg-slate-900/60 p-3 rounded-lg border border-slate-800/80 leading-relaxed">
                {item}
              </li>
            ))}
          </ul>
        </div>

        {/* Gaps */}
        <div className="glass-panel p-5 rounded-2xl border border-amber-500/20 shadow-lg">
          <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Gaps & Misconceptions ({gaps.length})
          </h3>
          <ul className="space-y-2">
            {gaps.map((item, idx) => (
              <li key={idx} className="text-xs text-slate-200 bg-slate-900/60 p-3 rounded-lg border border-slate-800/80 leading-relaxed">
                {item}
              </li>
            ))}
          </ul>
        </div>

        {/* Next Steps */}
        <div className="glass-panel p-5 rounded-2xl border border-blue-500/20 shadow-lg">
          <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
            <ArrowRightCircle className="w-4 h-4 text-blue-400" />
            Recommended Next Steps ({next.length})
          </h3>
          <ul className="space-y-2">
            {next.map((item, idx) => (
              <li key={idx} className="text-xs text-slate-200 bg-slate-900/60 p-3 rounded-lg border border-slate-800/80 leading-relaxed">
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

