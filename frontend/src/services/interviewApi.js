import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 45000, // 45 seconds to accommodate LLM inference
});

/**
 * Initiates a new adaptive interview session.
 * @param {Object} config - { role, experience, interview_type, topics, difficulty, number_of_questions }
 * @returns {Promise<Object>} - StartInterviewResponse
 */
export async function startInterview(config) {
  const response = await apiClient.post('/api/interviews/start', config);
  return response.data;
}

/**
 * Submits the candidate's answer to the active question.
 * @param {string} interviewId - Unique interview session ID
 * @param {string} answer - Candidate's technical answer
 * @returns {Promise<Object>} - SubmitAnswerResponse
 */
export async function submitAnswer(interviewId, answer) {
  const response = await apiClient.post(`/api/interviews/${interviewId}/answer`, { answer });
  return response.data;
}

/**
 * Retrieves metadata and status for a specific interview session.
 * @param {string} interviewId
 * @returns {Promise<Object>} - InterviewSummaryResponse
 */
export async function getInterview(interviewId) {
  const response = await apiClient.get(`/api/interviews/${interviewId}`);
  return response.data;
}

/**
 * Retrieves the final structured assessment report for a completed interview.
 * @param {string} interviewId
 * @returns {Promise<Object>} - ReportResponse
 */
export async function getReport(interviewId) {
  const response = await apiClient.get(`/api/interviews/${interviewId}/report`);
  return response.data;
}

export default {
  startInterview,
  submitAnswer,
  getInterview,
  getReport,
};
