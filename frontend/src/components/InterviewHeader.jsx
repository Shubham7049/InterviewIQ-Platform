import { Terminal } from 'lucide-react';

export default function InterviewHeader({
  role = 'Software Developer',
  interviewType = 'Technical',
  currentQuestionNumber = 1,
  totalQuestions = 5,
  difficulty = 'medium',
}) {
  const difficultyColors = {
    easy: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    medium: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    hard: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  };

  const diffColor = difficultyColors[difficulty?.toLowerCase()] || difficultyColors.medium;

  return (
    <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-10 px-6 py-4">
      <div className="max-w-5xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-500 font-bold">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold tracking-tight text-white">InterviewIQ</span>
              <span className="text-[10px] uppercase font-bold tracking-widest bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/20">
                Agentic AI
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              {role} • <span className="capitalize">{interviewType}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 self-end sm:self-auto">
          <div className={`text-xs font-semibold px-2.5 py-1 rounded-lg border capitalize ${diffColor}`}>
            {difficulty} Level
          </div>
          <div className="text-xs font-medium px-3 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700">
            Q{currentQuestionNumber} / {totalQuestions}
          </div>
        </div>
      </div>
    </header>
  );
}
