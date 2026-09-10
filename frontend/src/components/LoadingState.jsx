import { Loader2 } from 'lucide-react';

export default function LoadingState({ message = 'Loading...', submessage = '' }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <div className="relative flex items-center justify-center mb-4">
        <div className="w-16 h-16 rounded-full border-4 border-blue-500/20 border-t-blue-500 animate-spin" />
        <Loader2 className="w-8 h-8 text-blue-500 absolute animate-pulse" />
      </div>
      <h3 className="text-lg font-semibold text-slate-100">{message}</h3>
      {submessage && (
        <p className="text-sm text-slate-400 mt-1 max-w-sm">{submessage}</p>
      )}
    </div>
  );
}
