import { useState } from 'react';
import { Send, AlertCircle, CornerDownLeft } from 'lucide-react';

export default function AnswerBox({ onSubmit, isSubmitting = false }) {
  const [answer, setAnswer] = useState('');
  const [validationError, setValidationError] = useState('');

  const wordCount = answer.trim() ? answer.trim().split(/\s+/).length : 0;
  const charCount = answer.length;

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (isSubmitting) return;

    if (!answer.trim()) {
      setValidationError('Please enter an answer before submitting.');
      return;
    }

    setValidationError('');
    onSubmit(answer.trim());
  };

  const handleKeyDown = (e) => {
    // Support Ctrl+Enter or Cmd+Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <label htmlFor="answer-input" className="text-sm font-semibold text-slate-200">
          Your Technical Answer
        </label>
        <div className="text-xs text-slate-400 space-x-2 font-mono">
          <span>{wordCount} words</span>
          <span>•</span>
          <span>{charCount} chars</span>
        </div>
      </div>

      <textarea
        id="answer-input"
        rows={8}
        disabled={isSubmitting}
        value={answer}
        onChange={(e) => {
          setAnswer(e.target.value);
          if (validationError) setValidationError('');
        }}
        onKeyDown={handleKeyDown}
        placeholder="Type your explanation, design trade-offs, architecture reasoning, or code thoughts here..."
        className="w-full bg-slate-900/90 border border-slate-700 rounded-xl p-4 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-y text-base font-normal leading-relaxed disabled:opacity-50"
      />

      {validationError && (
        <p className="text-xs text-red-400 flex items-center space-x-1 font-medium">
          <AlertCircle className="w-3.5 h-3.5" />
          <span>{validationError}</span>
        </p>
      )}

      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
        <span className="text-xs text-slate-400 flex items-center space-x-1 order-2 sm:order-1">
          <CornerDownLeft className="w-3.5 h-3.5 opacity-60" />
          <span>Pro tip: Press <kbd className="px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 font-mono text-[10px]">Ctrl+Enter</kbd> to submit</span>
        </span>

        <button
          type="button"
          onClick={handleSubmit}
          disabled={isSubmitting || !answer.trim()}
          className="w-full sm:w-auto order-1 sm:order-2 inline-flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl font-semibold text-sm bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:pointer-events-none transition-all cursor-pointer"
        >
          <Send className="w-4 h-4" />
          <span>{isSubmitting ? 'Evaluating Answer...' : 'Submit Answer'}</span>
        </button>
      </div>
    </div>
  );
}
