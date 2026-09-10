import { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import InterviewHeader from '../components/InterviewHeader';
import QuestionCard from '../components/QuestionCard';
import AnswerBox from '../components/AnswerBox';
import ProgressBar from '../components/ProgressBar';
import LoadingState from '../components/LoadingState';
import ErrorMessage from '../components/ErrorMessage';
import { submitAnswer, getInterview } from '../services/interviewApi';

export default function Interview() {
  const { interviewId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  // Initial data passed from Home.jsx or restored via API
  const [session, setSession] = useState(location.state?.initialData || null);
  const [config, setConfig] = useState(location.state?.config || null);
  const [currentQuestion, setCurrentQuestion] = useState(
    location.state?.initialData?.question || null
  );
  const [questionNumber, setQuestionNumber] = useState(
    location.state?.initialData?.current_question_number || 1
  );
  const [totalQuestions, setTotalQuestions] = useState(
    location.state?.initialData?.total_questions || 5
  );
  const [currentDifficulty, setCurrentDifficulty] = useState(
    location.state?.initialData?.question?.difficulty || 'medium'
  );

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingSession, setIsLoadingSession] = useState(!location.state?.initialData);
  const [error, setError] = useState('');
  const [evaluationFeedback, setEvaluationFeedback] = useState(null);

  // If user navigated directly or refreshed, restore session from backend
  useEffect(() => {
    if (!session && interviewId) {
      const fetchSession = async () => {
        setIsLoadingSession(true);
        setError('');
        try {
          const data = await getInterview(interviewId);
          setSession(data);
          setConfig(data.configuration);
          setQuestionNumber(data.current_question_number);
          setTotalQuestions(data.configuration?.number_of_questions || 5);
          setCurrentDifficulty(data.configuration?.difficulty || 'medium');

          if (data.status === 'completed') {
            navigate(`/report/${interviewId}`);
            return;
          }
        } catch (err) {
          console.error('Error fetching interview session:', err);
          setError(
            err.response?.status === 404
              ? 'Interview session not found.'
              : 'Failed to load interview session. Please verify connection.'
          );
        } finally {
          setIsLoadingSession(false);
        }
      };
      fetchSession();
    }
  }, [interviewId, session, navigate]);

  const handleAnswerSubmit = async (answerText) => {
    setIsSubmitting(true);
    setError('');
    setEvaluationFeedback(null);

    try {
      const response = await submitAnswer(interviewId, answerText);

      // Show temporary adaptive evaluation indicator
      if (response.evaluation) {
        setEvaluationFeedback({
          score: response.evaluation.overall_score,
          feedback: response.evaluation.feedback,
          action: response.adaptive_decision?.action,
        });
      }

      if (response.is_completed) {
        // Interview finished -> navigate to final report
        setTimeout(() => {
          navigate(`/report/${interviewId}`);
        }, 1200);
      } else {
        // Continue to next question
        setTimeout(() => {
          setCurrentQuestion(response.next_question);
          setQuestionNumber(response.current_question_number + 1);
          if (response.next_question?.difficulty) {
            setCurrentDifficulty(response.next_question.difficulty);
          }
          setEvaluationFeedback(null);
          setIsSubmitting(false);
        }, 1200);
      }
    } catch (err) {
      console.error('Error submitting answer:', err);
      if (err.response?.status === 409) {
        // Already completed
        navigate(`/report/${interviewId}`);
      } else {
        setError(
          err.response?.data?.detail ||
          'Failed to process answer. Please check your connection and try again.'
        );
        setIsSubmitting(false);
      }
    }
  };

  if (isLoadingSession) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <LoadingState message="Loading interview session..." submessage="Connecting to agent state..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 text-slate-100 flex flex-col">
      {/* Persistent Interview Header */}
      <InterviewHeader
        role={config?.role || 'Software Developer'}
        interviewType={config?.interview_type || 'Technical'}
        currentQuestionNumber={questionNumber}
        totalQuestions={totalQuestions}
        difficulty={currentDifficulty}
      />

      <main className="max-w-4xl mx-auto px-6 py-8 flex-1 w-full space-y-6">
        {/* Progress Bar */}
        <ProgressBar current={questionNumber} total={totalQuestions} />

        {error && <ErrorMessage message={error} />}

        {/* Evaluating / Adaptive Transition Toast */}
        {isSubmitting && (
          <div className="bg-blue-600/10 border border-blue-500/30 rounded-2xl p-6 text-center animate-pulse">
            <div className="flex items-center justify-center space-x-2 text-blue-400 font-semibold mb-1">
              <Sparkles className="w-5 h-5 animate-spin" />
              <span>
                {evaluationFeedback
                  ? 'Your response has been evaluated. The next question is being selected based on your performance...'
                  : 'AI is evaluating your technical answer...'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {evaluationFeedback
                ? 'Calibrating topic depth and adaptive difficulty based on candidate performance.'
                : 'Assessing correctness, technical depth, and communication clarity.'}
            </p>
          </div>
        )}

        {/* Question Card */}
        {currentQuestion ? (
          <QuestionCard
            question={currentQuestion}
            questionNumber={questionNumber}
            totalQuestions={totalQuestions}
          />
        ) : (
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-2xl p-8 text-center">
            <p className="text-sm text-slate-400">Loading current question...</p>
          </div>
        )}

        {/* Answer Input Area */}
        <AnswerBox onSubmit={handleAnswerSubmit} isSubmitting={isSubmitting} />
      </main>
    </div>
  );
}
