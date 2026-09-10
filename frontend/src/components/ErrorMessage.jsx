import { AlertCircle, RefreshCw } from 'lucide-react';

export default function ErrorMessage({ message, onRetry = null }) {
  if (!message) return null;

  return (
    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start space-x-3 text-red-400">
      <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <p className="text-sm font-medium">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 inline-flex items-center space-x-1.5 text-xs font-semibold text-red-300 hover:text-white bg-red-500/20 hover:bg-red-500/30 px-2.5 py-1 rounded-md transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
        )}
      </div>
    </div>
  );
}
