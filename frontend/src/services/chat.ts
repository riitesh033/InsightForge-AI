import api from "@/lib/api";


// ============================================================
// Types
// ============================================================

export interface ChatMessage {
  id?: number;
  session_id?: number;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}


export interface ChatSession {
  id: number;
  dataset_id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
}


export interface ChatResponse {
  session_id: number;
  dataset_id: number;
  answer: string;
  messages: ChatMessage[];
}


export interface ChatSessionMessagesResponse {
  session_id: number;
  dataset_id: number;
  messages: ChatMessage[];
}


// ============================================================
// Get Sessions
// ============================================================

export async function getChatSessions(
  datasetId: number
): Promise<ChatSession[]> {

  const response =
    await api.get<ChatSession[]>(
      `/chat/${datasetId}/sessions`
    );

  return response.data;
}


// ============================================================
// Create New Session
// ============================================================

export async function createChatSession(
  datasetId: number
): Promise<ChatSession> {

  const response =
    await api.post<ChatSession>(
      `/chat/${datasetId}/sessions`
    );

  return response.data;
}


// ============================================================
// Get Session Messages
// ============================================================

export async function getChatSession(
  sessionId: number
): Promise<ChatSessionMessagesResponse> {

  const response =
    await api.get<ChatSessionMessagesResponse>(
      `/chat/sessions/${sessionId}`
    );

  return response.data;
}


// ============================================================
// Delete Session
// ============================================================

export async function deleteChatSession(
  sessionId: number
): Promise<void> {

  await api.delete(
    `/chat/sessions/${sessionId}`
  );
}


// ============================================================
// Send Message
// ============================================================

export async function sendChatMessage(
  datasetId: number,
  sessionId: number,
  message: string
): Promise<ChatResponse> {

  const response =
    await api.post<ChatResponse>(
      `/chat/${datasetId}`,
      {
        message,
        session_id: sessionId,
      }
    );

  return response.data;
}