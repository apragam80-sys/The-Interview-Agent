/**
 * API Service for interacting strictly with POST /api/interview.
 * Provides client wrappers for session initialization and turn progression.
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

/**
 * Execute HTTP POST request to /api/interview.
 * 
 * @param {Object} payload - The request payload ({ sessionId, candidate } or { sessionId, message })
 * @returns {Promise<Object>} The API response ({ reply, done, feedback? })
 */
export async function sendInterviewRequest(payload) {
  // TODO: Implement HTTP POST fetch call to POST /api/interview
  const response = await fetch(`${API_BASE_URL}/api/interview`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Interview API Error (${response.status}): ${errorText}`);
  }

  return await response.json();
}

/**
 * Start an interview session (Turn 1).
 * 
 * @param {string} sessionId - Unique session identifier
 * @param {Object} candidateProfile - Full candidate profile JSON
 */
export async function startInterviewSession(sessionId, candidateProfile) {
  // TODO: Wrap Turn 1 request
  return await sendInterviewRequest({
    sessionId,
    candidate: candidateProfile,
  });
}

/**
 * Send candidate answer for a conversation turn (Turn N).
 * 
 * @param {string} sessionId - Unique session identifier
 * @param {string} message - Candidate answer string
 */
export async function sendCandidateAnswer(sessionId, message) {
  // TODO: Wrap Turn N request
  return await sendInterviewRequest({
    sessionId,
    message,
  });
}
