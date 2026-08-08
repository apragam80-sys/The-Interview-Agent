import React, { useState } from 'react';
import { User, Briefcase, GraduationCap, Sparkles, ChevronRight, Search } from 'lucide-react';
import candidatesData from '../data/candidates.json';

/**
 * CandidateSelector Component.
 * 
 * Props:
 * @param {Function} onSelectCandidate - Callback function invoked when a candidate is chosen: (candidate) => void
 * @param {boolean} isLoading - Loading state indicator
 */
export default function CandidateSelector({ onSelectCandidate, isLoading = false }) {
  const [searchTerm, setSearchTerm] = useState('');
  const candidates = candidatesData.candidates || [];

  // TODO: Implement advanced filtering by experience level and signals
  const filteredCandidates = candidates.filter((c) => {
    const name = c?.member?.name || '';
    const role = c?.member?.jobRole || '';
    return name.toLowerCase().includes(searchTerm.toLowerCase()) ||
           role.toLowerCase().includes(searchTerm.toLowerCase());
  });

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-blue-500/20 shadow-lg">
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-semibold w-fit mb-2">
          <Sparkles className="w-3.5 h-3.5" />
          Candidate Benchmark Selector
        </div>
        <h1 className="text-2xl font-bold text-white">Select Candidate Profile</h1>
        <p className="text-sm text-slate-400 mt-1">
          Choose a benchmark candidate from <code className="text-blue-400 font-mono text-xs">candidates.json</code> to initialize an adaptive interview.
        </p>

        {/* Search Bar */}
        <div className="mt-4 relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search candidate by name or role..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>
      </div>

      {/* Candidate Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredCandidates.map((candidate) => {
          const { member, signals } = candidate;
          return (
            <div
              key={member.id}
              className="glass-panel p-5 rounded-2xl border border-slate-800 hover:border-blue-500/40 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-blue-400 border border-slate-700">
                    {member.id}
                  </span>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    {member.yearsExperience} yrs exp
                  </span>
                </div>

                <h2 className="text-lg font-bold text-white">{member.name}</h2>
                <div className="flex items-center gap-1.5 text-xs text-slate-300 mt-1">
                  <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                  <span>{member.jobRole}</span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-0.5">
                  <GraduationCap className="w-3.5 h-3.5 text-slate-500" />
                  <span className="truncate">{member.education}</span>
                </div>

                {/* Signals Bar */}
                <div className="mt-4 p-2.5 bg-slate-900 rounded-xl border border-slate-800 grid grid-cols-3 gap-2 text-center text-xs">
                  <div>
                    <div className="text-[10px] text-slate-400">Commits</div>
                    <div className="font-bold text-white font-mono">{signals.commitDays}/31</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">Completed</div>
                    <div className="font-bold text-emerald-400 font-mono">{signals.missionsCompleted}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-400">1st Try</div>
                    <div className="font-bold text-blue-400 font-mono">{signals.missionsFirstTry}</div>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => onSelectCandidate(candidate)}
                disabled={isLoading}
                className="mt-5 w-full py-2 px-4 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl flex items-center justify-center gap-1.5 transition-all disabled:opacity-50"
              >
                <span>Start Technical Interview</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
