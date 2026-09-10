import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Terminal, Shield, Zap, Sparkles } from 'lucide-react';
import InterviewSetup from '../components/InterviewSetup';
import { startInterview } from '../services/interviewApi';

export default function Home() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleStart = async (config) => {
    setIsLoading(true);
    setError('');
    try {
      const response = await startInterview(config);
      // Navigate to interview page and pass initial question & metadata
      navigate(`/interview/${response.interview_id}`, {
        state: {
          initialData: response,
          config,
        },
      });
    } catch (err) {
      console.error('Failed to start interview:', err);
      const errMsg =
        err.response?.data?.detail ||
        'Unable to connect to the interview service. Please verify the backend is running.';
      setError(errMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Top Navigation */}
      <header className="px-6 py-4 border-b border-slate-800/80 bg-slate-900/40 backdrop-blur-md">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
              <Terminal className="w-5 h-5" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">InterviewIQ</span>
          </div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700/60">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>Agentic AI Assessment</span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-4xl mx-auto px-6 py-12 flex-1 w-full">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white mb-3">
            Adaptive Technical Assessment Platform
          </h1>
          <p className="text-sm sm:text-base text-slate-400 leading-relaxed">
            Experience a realistic, dynamic interview. Powered by LangGraph state orchestration,
            InterviewIQ evaluates depth, diagnoses gaps, and adapts difficulty in real-time.
          </p>
        </div>

        {/* Configuration Card */}
        <div className="bg-slate-850 bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-10 shadow-2xl shadow-black/40">
          <div className="border-b border-slate-800/80 pb-4 mb-6">
            <h2 className="text-lg font-bold text-white">Configure Your Session</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Select your target role, focus domains, and desired question count to begin.
            </p>
          </div>

          <InterviewSetup onStart={handleStart} isLoading={isLoading} error={error} />
        </div>

        {/* Feature Badges */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8">
          <div className="bg-slate-800/40 border border-slate-800/60 rounded-2xl p-4 flex items-center space-x-3">
            <Zap className="w-5 h-5 text-blue-400 flex-shrink-0" />
            <div>
              <h4 className="text-xs font-bold text-slate-200">Dynamic Adaptation</h4>
              <p className="text-[11px] text-slate-400">Questions calibrate to your technical depth</p>
            </div>
          </div>
          <div className="bg-slate-800/40 border border-slate-800/60 rounded-2xl p-4 flex items-center space-x-3">
            <Shield className="w-5 h-5 text-indigo-400 flex-shrink-0" />
            <div>
              <h4 className="text-xs font-bold text-slate-200">Rigor & Accuracy</h4>
              <p className="text-[11px] text-slate-400">Evaluates conceptual trade-offs, not keywords</p>
            </div>
          </div>
          <div className="bg-slate-800/40 border border-slate-800/60 rounded-2xl p-4 flex items-center space-x-3">
            <Sparkles className="w-5 h-5 text-purple-400 flex-shrink-0" />
            <div>
              <h4 className="text-xs font-bold text-slate-200">Structured Scorecard</h4>
              <p className="text-[11px] text-slate-400">Actionable growth roadmap and hiring readiness</p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-6 text-center text-xs text-slate-500">
        InterviewIQ • Production Agentic AI Interview Engine
      </footer>
    </div>
  );
}
