import { Layers } from 'lucide-react';

export default function QuestionCard({ question, questionNumber = 1, totalQuestions = 5 }) {
  if (!question) return null;

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
      {/* Decorative gradient border glow */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 opacity-80" />

      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center space-x-1.5 text-xs font-semibold px-2.5 py-1 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Layers className="w-3.5 h-3.5" />
            <span>{question.topic}</span>
          </span>
          {question.question_type && (
            <span className="text-xs font-medium px-2 py-0.5 rounded-md bg-slate-700/60 text-slate-300 capitalize">
              {question.question_type}
            </span>
          )}
        </div>
        <span className="text-xs font-semibold text-slate-400">
          Question {questionNumber} of {totalQuestions}
        </span>
      </div>

      <h2 className="text-xl sm:text-2xl font-semibold text-slate-100 leading-relaxed">
        {question.question_text}
      </h2>
    </div>
  );
}
