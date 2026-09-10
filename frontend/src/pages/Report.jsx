import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  BookOpen,
  ArrowRight,
  Terminal,
  RotateCcw,
} from 'lucide-react';
import { getReport } from '../services/interviewApi';
import LoadingState from '../components/LoadingState';
import ErrorMessage from '../components/ErrorMessage';

export default function Report() {
  const { interviewId } = useParams();
  const navigate = useNavigate();

  const [report, setReport] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchReport = async () => {
      setIsLoading(true);
      setError('');
      try {
        const response = await getReport(interviewId);
        setReport(response.report);
      } catch (err) {
        console.error('Error fetching report:', err);
        if (err.response?.status === 400) {
          setError('This interview is still in progress. The assessment report has not been generated yet.');
        } else if (err.response?.status === 404) {
          setError('Interview or assessment report not found.');
        } else {
          setError('Unable to load assessment report. Please verify connection.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    if (interviewId) {
      fetchReport();
    }
  }, [interviewId]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <LoadingState
          message="Loading assessment report..."
          submessage="Synthesizing candidate scorecard..."
        />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-6 text-center">
        <div className="max-w-md w-full space-y-4">
          <ErrorMessage message={error || 'Report unavailable.'} />
          <div className="pt-2 flex justify-center space-x-3">
            <button
              onClick={() => navigate('/')}
              className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition-all inline-flex items-center space-x-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Back to Home</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Convert 0-10 score to 0-100 percentage
  const scoreOutOf100 = Math.round(report.overall_score * 10);

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
    if (score >= 60) return 'text-blue-400 border-blue-500/30 bg-blue-500/10';
    if (score >= 40) return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
    return 'text-rose-400 border-rose-500/30 bg-rose-500/10';
  };

  const getReadinessColor = (readiness) => {
    const text = (readiness || '').toLowerCase();
    if (text.includes('strong') || text.includes('ready')) {
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    }
    if (text.includes('needs')) {
      return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
    }
    return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Top Header */}
      <header className="px-6 py-4 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white">InterviewIQ</span>
              <p className="text-xs text-slate-400">Technical Assessment Scorecard</p>
            </div>
          </div>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold border border-slate-700 transition-all flex items-center space-x-1.5 cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>New Interview</span>
          </button>
        </div>
      </header>

      {/* Report Dashboard Main */}
      <main className="max-w-5xl mx-auto px-6 py-10 flex-1 w-full space-y-8">
        {/* Executive Overview Banner */}
        <div className="bg-slate-850 bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <span className="text-xs uppercase font-bold tracking-wider text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2.5 py-0.5 rounded-full">
                  Verified Assessment
                </span>
                <span className="text-xs text-slate-500 font-mono">ID: {report.interview_id}</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
                Technical Performance Report
              </h1>
              <p className="text-sm text-slate-400 max-w-xl leading-relaxed">
                {report.final_summary}
              </p>
            </div>

            {/* Score Metric Card */}
            <div className="flex items-center space-x-4 self-start sm:self-center">
              <div
                className={`p-6 rounded-2xl border text-center flex flex-col items-center justify-center min-w-[140px] shadow-lg ${getScoreColor(
                  scoreOutOf100
                )}`}
              >
                <span className="text-4xl sm:text-5xl font-black tracking-tight">
                  {scoreOutOf100}
                </span>
                <span className="text-[11px] uppercase tracking-wider font-semibold opacity-75 mt-1">
                  Overall Score / 100
                </span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-400 font-medium">Hiring Recommendation:</span>
              <span
                className={`text-xs font-bold px-3 py-1 rounded-full border capitalize ${getReadinessColor(
                  report.hiring_readiness
                )}`}
              >
                {report.hiring_readiness}
              </span>
            </div>
            <span className="text-xs text-slate-500">Evaluated via LangGraph Adaptive State Engine</span>
          </div>
        </div>

        {/* Topic Breakdown Grid */}
        {report.topic_scores && Object.keys(report.topic_scores).length > 0 && (
          <div className="bg-slate-800/60 border border-slate-700/60 rounded-3xl p-6 sm:p-8 space-y-4">
            <div className="flex items-center space-x-2 text-white font-bold text-base">
              <BarChart3 className="w-5 h-5 text-blue-400" />
              <h3>Topic Performance Breakdown</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              {Object.entries(report.topic_scores).map(([topic, score]) => {
                const topicScore100 = Math.round(score * 10);
                return (
                  <div
                    key={topic}
                    className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 space-y-2"
                  >
                    <div className="flex justify-between items-center text-sm font-semibold">
                      <span className="text-slate-200">{topic}</span>
                      <span className="text-blue-400 font-mono font-bold">{topicScore100}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(topicScore100, 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Strengths & Weaknesses 2-Column Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {/* Key Strengths */}
          <div className="bg-slate-800/50 border border-slate-700/60 rounded-3xl p-6 sm:p-7 space-y-4">
            <div className="flex items-center space-x-2 text-emerald-400 font-bold text-base">
              <CheckCircle2 className="w-5 h-5" />
              <h3>Demonstrated Strengths</h3>
            </div>
            <ul className="space-y-2.5">
              {report.strengths && report.strengths.length > 0 ? (
                report.strengths.map((st, i) => (
                  <li key={i} className="text-sm text-slate-300 flex items-start space-x-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-2 flex-shrink-0" />
                    <span>{st}</span>
                  </li>
                ))
              ) : (
                <li className="text-sm text-slate-500">No specific strengths documented.</li>
              )}
            </ul>
          </div>

          {/* Growth Areas */}
          <div className="bg-slate-800/50 border border-slate-700/60 rounded-3xl p-6 sm:p-7 space-y-4">
            <div className="flex items-center space-x-2 text-amber-400 font-bold text-base">
              <AlertTriangle className="w-5 h-5" />
              <h3>Areas for Growth</h3>
            </div>
            <ul className="space-y-2.5">
              {report.weaknesses && report.weaknesses.length > 0 ? (
                report.weaknesses.map((wk, i) => (
                  <li key={i} className="text-sm text-slate-300 flex items-start space-x-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-2 flex-shrink-0" />
                    <span>{wk}</span>
                  </li>
                ))
              ) : (
                <li className="text-sm text-slate-500">No major knowledge gaps noted.</li>
              )}
            </ul>
          </div>
        </div>

        {/* Summaries: Technical & Communication */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div className="bg-slate-800/40 border border-slate-700/60 rounded-3xl p-6 space-y-2">
            <h4 className="text-xs uppercase font-bold tracking-wider text-slate-400">Technical Synthesis</h4>
            <p className="text-sm text-slate-300 leading-relaxed">{report.technical_summary}</p>
          </div>
          <div className="bg-slate-800/40 border border-slate-700/60 rounded-3xl p-6 space-y-2">
            <h4 className="text-xs uppercase font-bold tracking-wider text-slate-400">Communication Synthesis</h4>
            <p className="text-sm text-slate-300 leading-relaxed">{report.communication_summary}</p>
          </div>
        </div>

        {/* Recommended Learning Roadmap */}
        {report.recommended_topics && report.recommended_topics.length > 0 && (
          <div className="bg-slate-800/40 border border-slate-700/60 rounded-3xl p-6 sm:p-7 space-y-3">
            <div className="flex items-center space-x-2 text-indigo-400 font-bold text-sm">
              <BookOpen className="w-4 h-4" />
              <h4>Recommended Action Roadmap</h4>
            </div>
            <div className="flex flex-wrap gap-2 pt-1">
              {report.recommended_topics.map((top, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1.5 rounded-xl bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-xs font-semibold"
                >
                  {top}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Action Button */}
        <div className="text-center pt-4 pb-8">
          <button
            onClick={() => navigate('/')}
            className="px-8 py-3.5 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm shadow-xl shadow-blue-500/25 transition-all inline-flex items-center space-x-2 cursor-pointer"
          >
            <span>Start Another Assessment</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </main>

      <footer className="border-t border-slate-800/60 py-6 text-center text-xs text-slate-500">
        InterviewIQ • Technical Assessment System
      </footer>
    </div>
  );
}
