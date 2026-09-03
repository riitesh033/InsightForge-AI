import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import {
  Send,
  Bot,
  User,
  Sparkles,
  Plus,
  Trash2,
  MessageSquare,
} from "lucide-react";

import {
  Dataset,
  getDatasets,
} from "@/services/dataset";

import {
  ChatMessage,
  ChatSession,
  createChatSession,
  deleteChatSession,
  getChatSession,
  getChatSessions,
  sendChatMessage,
} from "@/services/chat";


export default function AIChatPage() {
  const { datasetId: datasetIdParam } =
    useParams<{ datasetId?: string }>();

  const routeDatasetId = datasetIdParam
    ? Number(datasetIdParam)
    : null;


  // ==========================================================
  // Dataset
  // ==========================================================

  const [datasets, setDatasets] =
    useState<Dataset[]>([]);

  const [selectedDatasetId, setSelectedDatasetId] =
    useState<number | "">("");


  // ==========================================================
  // Chat Sessions
  // ==========================================================

  const [sessions, setSessions] =
    useState<ChatSession[]>([]);

  const [selectedSessionId, setSelectedSessionId] =
    useState<number | null>(null);


  // ==========================================================
  // Messages
  // ==========================================================

  const [messages, setMessages] =
    useState<ChatMessage[]>([]);

  const [message, setMessage] =
    useState("");


  // ==========================================================
  // Loading
  // ==========================================================

  const [loadingDatasets, setLoadingDatasets] =
    useState(true);

  const [loadingSessions, setLoadingSessions] =
    useState(false);

  const [loadingMessages, setLoadingMessages] =
    useState(false);

  const [sending, setSending] =
    useState(false);


  const [error, setError] =
    useState("");


  // ==========================================================
  // Load Datasets
  // ==========================================================

  useEffect(() => {
    loadDatasets();
  }, []);


  async function loadDatasets() {
    try {
      setLoadingDatasets(true);
      setError("");

      const response = await getDatasets();

      setDatasets(response.items);

      if (response.items.length > 0) {
        /*
         * If a dataset ID was provided in the URL,
         * select that dataset.
         *
         * Example:
         * /dashboard/ai-chat/2
         *
         * Otherwise select the first dataset.
         */
        const datasetFromRoute =
          routeDatasetId !== null
            ? response.items.find(
                (dataset) =>
                  dataset.id === routeDatasetId
              )
            : undefined;

        if (datasetFromRoute) {
          setSelectedDatasetId(
            datasetFromRoute.id
          );
        } else {
          setSelectedDatasetId(
            response.items[0].id
          );
        }
      } else {
        setSelectedDatasetId("");
        setSessions([]);
        setMessages([]);
      }
    } catch (err) {
      console.error(
        "Dataset loading error:",
        err
      );

      setError(
        "Failed to load datasets."
      );
    } finally {
      setLoadingDatasets(false);
    }
  }


  // ==========================================================
  // Load Sessions
  // ==========================================================

  useEffect(() => {
    if (
      typeof selectedDatasetId !== "number"
    ) {
      setSessions([]);
      setMessages([]);
      setSelectedSessionId(null);
      return;
    }

    loadSessions(selectedDatasetId);
  }, [selectedDatasetId]);


  async function loadSessions(
    datasetId: number
  ) {
    try {
      setLoadingSessions(true);
      setError("");

      const chatSessions =
        await getChatSessions(datasetId);

      setSessions(chatSessions);

      if (chatSessions.length > 0) {
        setSelectedSessionId(
          chatSessions[0].id
        );
      } else {
        setSelectedSessionId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error(
        "Chat sessions error:",
        err
      );

      setError(
        "Failed to load chat sessions."
      );
    } finally {
      setLoadingSessions(false);
    }
  }


  // ==========================================================
  // Load Selected Chat
  // ==========================================================

  useEffect(() => {
    if (
      selectedSessionId === null
    ) {
      return;
    }

    loadSession(selectedSessionId);
  }, [selectedSessionId]);


  async function loadSession(
    sessionId: number
  ) {
    try {
      setLoadingMessages(true);
      setError("");

      const response =
        await getChatSession(sessionId);

      setMessages(
        response.messages
      );
    } catch (err) {
      console.error(
        "Chat loading error:",
        err
      );

      setError(
        "Failed to load this chat."
      );
    } finally {
      setLoadingMessages(false);
    }
  }


  // ==========================================================
  // New Chat
  // ==========================================================

  async function handleNewChat() {
    if (
      typeof selectedDatasetId !== "number"
    ) {
      setError(
        "Please select a dataset first."
      );

      return;
    }

    try {
      setError("");

      const session =
        await createChatSession(
          selectedDatasetId
        );

      setSessions((previous) => [
        session,
        ...previous,
      ]);

      setSelectedSessionId(
        session.id
      );

      setMessages([]);
    } catch (err) {
      console.error(
        "New chat error:",
        err
      );

      setError(
        "Failed to create a new chat."
      );
    }
  }


  // ==========================================================
  // Delete Chat
  // ==========================================================

  async function handleDeleteChat(
    sessionId: number
  ) {
    try {
      setError("");

      await deleteChatSession(
        sessionId
      );

      const remaining =
        sessions.filter(
          (session) =>
            session.id !== sessionId
        );

      setSessions(remaining);

      if (
        selectedSessionId === sessionId
      ) {
        if (remaining.length > 0) {
          setSelectedSessionId(
            remaining[0].id
          );
        } else {
          setSelectedSessionId(null);
          setMessages([]);
        }
      }
    } catch (err) {
      console.error(
        "Delete chat error:",
        err
      );

      setError(
        "Failed to delete chat."
      );
    }
  }


  // ==========================================================
  // Send Message
  // ==========================================================

  async function sendMessage(
    customMessage?: string
  ) {
    const question =
      customMessage ?? message;

    if (!question.trim()) {
      return;
    }

    if (
      typeof selectedDatasetId !== "number"
    ) {
      setError(
        "Please select a dataset first."
      );

      return;
    }

    let sessionId =
      selectedSessionId;

    try {
      setSending(true);
      setError("");

      // ------------------------------------------------------
      // Automatically create chat if none exists
      // ------------------------------------------------------

      if (sessionId === null) {
        const session =
          await createChatSession(
            selectedDatasetId
          );

        sessionId = session.id;

        setSessions((previous) => [
          session,
          ...previous,
        ]);

        setSelectedSessionId(
          session.id
        );
      }


      // ------------------------------------------------------
      // Optimistic User Message
      // ------------------------------------------------------

      const userMessage: ChatMessage = {
        role: "user",
        content: question.trim(),
      };

      setMessages((previous) => [
        ...previous,
        userMessage,
      ]);

      setMessage("");


      // ------------------------------------------------------
      // API
      // ------------------------------------------------------

      const response =
        await sendChatMessage(
          selectedDatasetId,
          sessionId,
          question.trim()
        );

      setMessages(
        response.messages
      );


      // ------------------------------------------------------
      // Refresh sessions
      // ------------------------------------------------------

      const updatedSessions =
        await getChatSessions(
          selectedDatasetId
        );

      setSessions(
        updatedSessions
      );
    } catch (err) {
      console.error(
        "Chat error:",
        err
      );

      setError(
        "Failed to get a response from InsightForge AI."
      );
    } finally {
      setSending(false);
    }
  }


  // ==========================================================
  // Suggestions
  // ==========================================================

  function handleSuggestion(
    prompt: string
  ) {
    sendMessage(prompt);
  }


  // ==========================================================
  // Render
  // ==========================================================

  return (
    <div className="flex h-[calc(100vh-7rem)] min-h-[700px] flex-col">

      {/* =====================================================
          Header
      ====================================================== */}

      <div className="mb-5">
        <h1 className="text-3xl font-bold text-foreground">
          AI Chat
        </h1>

        <p className="mt-1 text-muted-foreground">
          Interact with your AI Data Analyst.
        </p>
      </div>


      {/* =====================================================
          Main Chat Layout
      ====================================================== */}

      <div className="flex min-h-0 flex-1 overflow-hidden rounded-2xl border border-border bg-card shadow-sm">

        {/* ===================================================
            Chat Sidebar
        ==================================================== */}

        <aside className="flex w-72 shrink-0 flex-col border-r border-border bg-background">

          {/* Sidebar Header */}

          <div className="border-b border-border p-4">
            <button
              onClick={handleNewChat}
              disabled={
                typeof selectedDatasetId !== "number"
              }
              className="
                flex
                w-full
                items-center
                justify-center
                gap-2
                rounded-lg
                bg-primary
                px-4
                py-3
                font-medium
                text-primary-foreground
                transition
                hover:opacity-90
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              <Plus size={18} />

              New Chat
            </button>
          </div>


          {/* Sidebar Title */}

          <div className="px-4 pb-2 pt-5">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Chat History
            </p>
          </div>


          {/* Sessions */}

          <div className="flex-1 overflow-y-auto px-2 pb-4">

            {loadingSessions ? (
              <div className="px-3 py-6 text-center text-sm text-muted-foreground">
                Loading chats...
              </div>
            ) : sessions.length === 0 ? (
              <div className="px-4 py-8 text-center">

                <MessageSquare
                  className="mx-auto mb-3 text-muted-foreground"
                  size={28}
                />

                <p className="text-sm text-muted-foreground">
                  No previous chats.
                </p>

                <p className="mt-1 text-xs text-muted-foreground">
                  Start a new conversation.
                </p>

              </div>
            ) : (
              <div className="space-y-1">

                {sessions.map(
                  (session) => (
                    <div
                      key={session.id}
                      className={`
                        group
                        flex
                        items-center
                        gap-2
                        rounded-lg
                        px-3
                        py-3
                        transition
                        ${
                          selectedSessionId ===
                          session.id
                            ? "bg-primary/10 text-primary"
                            : "hover:bg-accent"
                        }
                      `}
                    >

                      <button
                        onClick={() =>
                          setSelectedSessionId(
                            session.id
                          )
                        }
                        className="min-w-0 flex-1 text-left"
                      >
                        <div className="flex items-center gap-2">

                          <MessageSquare
                            size={16}
                            className="shrink-0"
                          />

                          <span className="truncate text-sm font-medium">
                            {session.title}
                          </span>

                        </div>

                        <p className="mt-1 pl-6 text-xs text-muted-foreground">
                          {new Date(
                            session.updated_at
                          ).toLocaleDateString()}
                        </p>
                      </button>


                      <button
                        onClick={() =>
                          handleDeleteChat(
                            session.id
                          )
                        }
                        className="
                          rounded-md
                          p-2
                          text-muted-foreground
                          opacity-0
                          transition
                          hover:bg-red-100
                          hover:text-red-600
                          group-hover:opacity-100
                          dark:hover:bg-red-950
                        "
                        title="Delete chat"
                      >
                        <Trash2 size={15} />
                      </button>

                    </div>
                  )
                )}

              </div>
            )}

          </div>

        </aside>


        {/* ===================================================
            Main Chat
        ==================================================== */}

        <section className="flex min-w-0 flex-1 flex-col">

          {/* Dataset Header */}

          <div className="border-b border-border bg-background p-4">

            <label className="mb-2 block text-sm font-medium text-foreground">
              Select Dataset
            </label>

            <select
              value={selectedDatasetId}
              onChange={(e) => {
                const value =
                  e.target.value
                    ? Number(e.target.value)
                    : "";

                setSelectedDatasetId(
                  value
                );

                setMessages([]);

                setSelectedSessionId(
                  null
                );
              }}
              disabled={
                loadingDatasets ||
                datasets.length === 0
              }
              className="
                w-full
                max-w-2xl
                rounded-lg
                border
                border-border
                bg-card
                px-4
                py-3
                text-foreground
                outline-none
                focus:border-primary
              "
            >

              {loadingDatasets ? (
                <option value="">
                  Loading datasets...
                </option>
              ) : datasets.length === 0 ? (
                <option value="">
                  No datasets available
                </option>
              ) : (
                datasets.map(
                  (dataset) => (
                    <option
                      key={dataset.id}
                      value={dataset.id}
                    >
                      {dataset.original_filename}
                    </option>
                  )
                )
              )}

            </select>

          </div>


          {/* Error */}

          {error && (
            <div className="mx-4 mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
              {error}
            </div>
          )}


          {/* =================================================
              Messages
          ================================================== */}

          <div className="min-h-0 flex-1 overflow-y-auto p-6 lg:p-8">

            {loadingMessages ? (
              <div className="flex h-full items-center justify-center">

                <p className="text-muted-foreground">
                  Loading conversation...
                </p>

              </div>
            ) : messages.length === 0 ? (
              <div className="flex h-full items-center justify-center">

                <div className="max-w-xl text-center">

                  <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground">
                    <Bot size={30} />
                  </div>

                  <h2 className="text-2xl font-semibold">
                    InsightForge AI
                  </h2>

                  <p className="mt-3 text-muted-foreground">
                    Ask questions about your dataset
                    using natural language.
                  </p>

                  <p className="mt-2 text-sm text-muted-foreground">
                    I can help with missing values,
                    duplicates, correlations,
                    outliers, statistics, and
                    data quality.
                  </p>

                </div>

              </div>
            ) : (
              <div className="mx-auto max-w-4xl space-y-6">

                {messages.map(
                  (chatMessage, index) => {
                    const isUser =
                      chatMessage.role ===
                      "user";

                    return (
                      <div
                        key={
                          chatMessage.id ??
                          `${chatMessage.role}-${index}`
                        }
                        className={
                          isUser
                            ? "flex justify-end"
                            : "flex items-start gap-3"
                        }
                      >

                        {!isUser && (
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                            <Bot size={19} />
                          </div>
                        )}

                        <div
                          className={
                            isUser
                              ? "flex max-w-[75%] items-end gap-3"
                              : "max-w-[75%]"
                          }
                        >

                          <div
                            className={
                              isUser
                                ? "rounded-2xl rounded-br-md bg-primary px-5 py-4 text-primary-foreground"
                                : "rounded-2xl rounded-bl-md bg-muted px-5 py-4 text-foreground"
                            }
                          >
                            <p className="whitespace-pre-wrap text-[15px] leading-7">
                              {chatMessage.content}
                            </p>
                          </div>

                          {isUser && (
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-muted text-foreground">
                              <User size={19} />
                            </div>
                          )}

                        </div>

                      </div>
                    );
                  }
                )}

                {sending && (
                  <div className="flex items-start gap-3">

                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      <Bot size={19} />
                    </div>

                    <div className="rounded-2xl rounded-bl-md bg-muted px-5 py-4 text-muted-foreground">
                      Thinking...
                    </div>

                  </div>
                )}

              </div>
            )}

          </div>


          {/* =================================================
              Input
          ================================================== */}

          <div className="border-t border-border bg-background p-5">

            <div className="mx-auto flex max-w-5xl gap-3">

              <input
                value={message}
                onChange={(e) =>
                  setMessage(
                    e.target.value
                  )
                }
                onKeyDown={(e) => {
                  if (
                    e.key === "Enter" &&
                    !e.shiftKey
                  ) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                disabled={
                  sending ||
                  typeof selectedDatasetId !==
                    "number"
                }
                placeholder="Ask InsightForge AI..."
                className="
                  flex-1
                  rounded-xl
                  border
                  border-border
                  bg-card
                  px-5
                  py-4
                  text-foreground
                  placeholder:text-muted-foreground
                  outline-none
                  transition
                  focus:border-primary
                  focus:ring-2
                  focus:ring-primary/20
                  disabled:opacity-50
                "
              />

              <button
                onClick={() =>
                  sendMessage()
                }
                disabled={
                  sending ||
                  !message.trim() ||
                  typeof selectedDatasetId !==
                    "number"
                }
                className="
                  flex
                  items-center
                  gap-2
                  rounded-xl
                  bg-primary
                  px-6
                  font-medium
                  text-primary-foreground
                  transition
                  hover:opacity-90
                  disabled:cursor-not-allowed
                  disabled:opacity-50
                "
              >
                <Send size={18} />

                {sending
                  ? "Sending..."
                  : "Send"}
              </button>

            </div>

          </div>

        </section>

      </div>


      {/* =====================================================
          Suggested Prompts
      ====================================================== */}

      <div className="mt-4 rounded-xl border border-border bg-card p-4">

        <div className="mb-3 flex items-center gap-2">

          <Sparkles
            className="text-primary"
            size={18}
          />

          <h2 className="font-semibold">
            Suggested Prompts
          </h2>

        </div>

        <div className="flex flex-wrap gap-2">

          {[
            "Summarize my dataset",
            "Detect missing values",
            "Find duplicate rows",
            "Show correlations",
            "Find outliers",
            "Generate business insights",
            "Recommend cleaning steps",
          ].map((prompt) => (
            <button
              key={prompt}
              onClick={() =>
                handleSuggestion(prompt)
              }
              disabled={
                sending ||
                typeof selectedDatasetId !==
                  "number"
              }
              className="
                rounded-full
                border
                border-border
                bg-background
                px-4
                py-2
                text-sm
                transition
                hover:bg-accent
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              {prompt}
            </button>
          ))}

        </div>

      </div>

    </div>
  );
}