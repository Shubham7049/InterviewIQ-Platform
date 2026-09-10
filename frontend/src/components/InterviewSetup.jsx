import { useState } from 'react';
import { Sparkles, ArrowRight, Check, AlertCircle } from 'lucide-react';

const ROLES = [
  'Software Developer',
  'Backend Developer',
  'Frontend Developer',
  'Full Stack Developer',
  'AI Engineer',
];

const EXPERIENCE_LEVELS = [
  { value: 'entry', label: 'Fresher (0–1 Years)' },
  { value: 'mid', label: 'Mid-Level (2–4 Years)' },
  { value: 'senior', label: 'Senior (5+ Years)' },
  { value: 'lead', label: 'Lead / Staff' },
];

const INTERVIEW_TYPES = [
  { value: 'technical', label: 'Technical & CS Fundamentals' },
  { value: 'system_design', label: 'System Design & Architecture' },
  { value: 'coding', label: 'Data Structures & Algorithms' },
  { value: 'mixed', label: 'Comprehensive Mixed' },
];

const TOPICS_LIST = [
  'OOP',
  'DSA',
  'DBMS',
  'Operating Systems',
  'Computer Networks',
  'System Design',
  'Distributed Systems',
  'Concurrency & Async',
];

const DIFFICULTIES = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
];

const QUESTION_COUNTS = [3, 5, 8, 10];

export default function InterviewSetup({ onStart, isLoading = false, error = '' }) {
  const [role, setRole] = useState('Software Developer');
  const [experience, setExperience] = useState('mid');
  const [interviewType, setInterviewType] = useState('technical');
  const [topics, setTopics] = useState(['OOP', 'DSA', 'DBMS']);
  const [difficulty, setDifficulty] = useState('medium');
  const [numberOfQuestions, setNumberOfQuestions] = useState(5);
  const [formError, setFormError] = useState('');

  const toggleTopic = (topic) => {
    if (topics.includes(topic)) {
      if (topics.length === 1) {
        setFormError('Please select at least one technical topic.');
        return;
      }
      setTopics(topics.filter((t) => t !== topic));
    } else {
      setTopics([...topics, topic]);
    }
    setFormError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!role.trim()) {
      setFormError('Please select or specify a target role.');
      return;
    }
    if (topics.length === 0) {
      setFormError('Please select at least one technical topic.');
      return;
    }
    setFormError('');
    onStart({
      role: role.trim(),
      experience,
      interview_type: interviewType,
      topics,
      difficulty,
      number_of_questions: numberOfQuestions,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Role Selection */}
      <div>
        <label className="block text-sm font-semibold text-slate-200 mb-2">
          Target Role
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          {ROLES.map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRole(r)}
              className={`px-4 py-3 rounded-xl border text-sm font-medium transition-all text-left flex items-center justify-between ${
                role === r
                  ? 'bg-blue-600/10 border-blue-500 text-blue-400 shadow-md shadow-blue-500/5'
                  : 'bg-slate-800/60 border-slate-700 text-slate-300 hover:border-slate-600 hover:bg-slate-800'
              }`}
            >
              <span>{r}</span>
              {role === r && <Check className="w-4 h-4 text-blue-400" />}
            </button>
          ))}
        </div>
      </div>

      {/* Experience Level */}
      <div>
        <label className="block text-sm font-semibold text-slate-200 mb-2">
          Experience Level
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {EXPERIENCE_LEVELS.map((exp) => (
            <button
              key={exp.value}
              type="button"
              onClick={() => setExperience(exp.value)}
              className={`px-3.5 py-2.5 rounded-xl border text-xs sm:text-sm font-medium transition-all text-center ${
                experience === exp.value
                  ? 'bg-blue-600/10 border-blue-500 text-blue-400 font-semibold'
                  : 'bg-slate-800/60 border-slate-700 text-slate-300 hover:border-slate-600 hover:bg-slate-800'
              }`}
            >
              {exp.label}
            </button>
          ))}
        </div>
      </div>

      {/* Interview Focus Type */}
      <div>
        <label className="block text-sm font-semibold text-slate-200 mb-2">
          Interview Assessment Type
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {INTERVIEW_TYPES.map((type) => (
            <button
              key={type.value}
              type="button"
              onClick={() => setInterviewType(type.value)}
              className={`px-4 py-2.5 rounded-xl border text-xs sm:text-sm font-medium transition-all text-left flex items-center justify-between ${
                interviewType === type.value
                  ? 'bg-blue-600/10 border-blue-500 text-blue-400 font-semibold'
                  : 'bg-slate-800/60 border-slate-700 text-slate-300 hover:border-slate-600 hover:bg-slate-800'
              }`}
            >
              <span>{type.label}</span>
              {interviewType === type.value && <Check className="w-4 h-4 text-blue-400" />}
            </button>
          ))}
        </div>
      </div>

      {/* Technical Topics Multi-select */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <label className="block text-sm font-semibold text-slate-200">
            Topics to Assess
          </label>
          <span className="text-xs text-slate-400 font-medium">Select multiple</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {TOPICS_LIST.map((topic) => {
            const isSelected = topics.includes(topic);
            return (
              <button
                key={topic}
                type="button"
                onClick={() => toggleTopic(topic)}
                className={`px-3.5 py-1.5 rounded-lg border text-xs font-semibold transition-all flex items-center space-x-1.5 ${
                  isSelected
                    ? 'bg-blue-600 text-white border-blue-500 shadow-sm'
                    : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:border-slate-600 hover:text-white'
                }`}
              >
                <span>{topic}</span>
                {isSelected && <Check className="w-3.5 h-3.5" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Difficulty & Question Count */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
        <div>
          <label className="block text-sm font-semibold text-slate-200 mb-2">
            Baseline Difficulty
          </label>
          <div className="grid grid-cols-3 gap-2">
            {DIFFICULTIES.map((diff) => (
              <button
                key={diff.value}
                type="button"
                onClick={() => setDifficulty(diff.value)}
                className={`px-3 py-2 rounded-xl border text-xs sm:text-sm font-semibold capitalize transition-all text-center ${
                  difficulty === diff.value
                    ? 'bg-blue-600/10 border-blue-500 text-blue-400'
                    : 'bg-slate-800/60 border-slate-700 text-slate-300 hover:border-slate-600'
                }`}
              >
                {diff.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-slate-200 mb-2">
            Number of Questions
          </label>
          <div className="grid grid-cols-4 gap-2">
            {QUESTION_COUNTS.map((count) => (
              <button
                key={count}
                type="button"
                onClick={() => setNumberOfQuestions(count)}
                className={`px-3 py-2 rounded-xl border text-xs sm:text-sm font-semibold transition-all text-center ${
                  numberOfQuestions === count
                    ? 'bg-blue-600/10 border-blue-500 text-blue-400'
                    : 'bg-slate-800/60 border-slate-700 text-slate-300 hover:border-slate-600'
                }`}
              >
                {count} Qs
              </button>
            ))}
          </div>
        </div>
      </div>

      {(formError || error) && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm p-3.5 rounded-xl flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{formError || error}</span>
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="w-full py-3.5 px-6 rounded-xl font-bold text-sm bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-50"
      >
        <Sparkles className="w-4 h-4" />
        <span>{isLoading ? 'Starting your interview...' : 'Start Technical Interview'}</span>
        {!isLoading && <ArrowRight className="w-4 h-4" />}
      </button>
    </form>
  );
}
