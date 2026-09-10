export default function ProgressBar({ current = 1, total = 5 }) {
  const percentage = Math.min(Math.round((current / total) * 100), 100);

  return (
    <div className="w-full">
      <div className="flex justify-between items-center text-xs font-semibold text-slate-400 mb-1.5">
        <span>Question {current} of {total}</span>
        <span>{percentage}% Completed</span>
      </div>
      <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden border border-slate-700/50">
        <div
          className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-500 ease-out rounded-full"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
