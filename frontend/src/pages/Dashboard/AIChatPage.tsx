import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import {
  Bot,
  Loader2,
  MessageSquare,
  PanelLeft,
  Plus,
  RefreshCw,
  Send,
  Sparkles,
  Trash2,
  User,
  X,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import PlanUpgradeLink from "@/components/payments/PlanUpgradeLink";
import { getApiErrorDetails, getApiErrorMessage, isPlanRestrictionError } from "@/lib/api";
import { getDatasets, type Dataset } from "@/services/dataset";
import {
  createChatSession,
  deleteChatSession,
  getChatSession,
  getChatSessions,
  sendChatMessage,
  type ChatMessage,
  type ChatSession,
} from "@/services/chat";

const SUGGESTED_PROMPTS = [
  "Summarize my dataset",
  "Detect missing values",
  "Find duplicate rows",
  "Show correlations",
  "Find outliers",
  "Generate business insights",
  "Recommend cleaning steps",
];

function getChatErrorMessage(error: unknown, fallback: string): string {
  const { status } = getApiErrorDetails(error);

  if (status === 401) {
    return "Your session has expired. Please sign in again.";
  }
  if (status === 403) {
    return isPlanRestrictionError(error)
      ? getApiErrorMessage(error, "This feature is not available on your current plan.")
      : "This feature is not available on your current plan.";
  }
  if (status === 404) {
    return "This conversation or dataset is no longer available. Refresh the history and try again.";
  }
  if (status === 429) {
    return getApiErrorMessage(error, "You have reached your usage limit. Please try again later.");
  }
  if (status !== undefined && status >= 500) {
    return "Something went wrong while processing your request. Please try again.";
  }

  if (error instanceof Error && /network|timeout|timed out/i.test(error.message)) {
    return "Unable to reach InsightForge AI. Check your connection and try again.";
  }

  return getApiErrorMessage(error, fallback);
}

function formatSessionDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  const now = new Date();
  const sameDay = date.toDateString() === now.toDateString();
  return sameDay
    ? date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })
    : date.toLocaleDateString([], { month: "short", day: "numeric" });
}

interface HistoryPanelProps {
  sessions: ChatSession[];
  activeSessionId: number | null;
  loading: boolean;
  creating: boolean;
  deletingId: number | null;
  error: string;
  canCreate: boolean;
  onCreate: () => void;
  onSelect: (session: ChatSession) => void;
  onDelete: (session: ChatSession) => void;
  onRetry: () => void;
  onClose?: () => void;
  busy: boolean;
}

function HistoryPanel({
  sessions,
  activeSessionId,
  loading,
  creating,
  deletingId,
  error,
  canCreate,
  onCreate,
  onSelect,
  onDelete,
  onRetry,
  onClose,
  busy,
}: HistoryPanelProps) {
  return (
    <div className="flex h-full min-h-0 flex-col bg-card">
      <div className="flex items-center justify-between gap-3 border-b border-border p-4">
        <div className="min-w-0">
          <h2 className="font-semibold text-foreground">Chat history</h2>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Conversations for this dataset
          </p>
        </div>
        {onClose && (
          <button
            type="button"
            aria-label="Close chat history"
            onClick={onClose}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            <X size={20} />
          </button>
        )}
      </div>

      <div className="border-b border-border p-4">
        <button
          type="button"
          onClick={onCreate}
          disabled={!canCreate || creating || loading || busy}
          className="flex min-h-11 w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 font-medium text-primary-foreground transition hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {creating ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Plus size={18} aria-hidden="true" />
          )}
          {creating ? "Creating chat..." : "New chat"}
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        {loading ? (
          <div role="status" className="flex items-center justify-center gap-2 px-3 py-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            Loading conversations...
          </div>
        ) : error ? (
          <div className="px-3 py-6 text-center">
            <p role="alert" className="text-sm text-destructive">{error}</p>
            <button
              type="button"
              onClick={onRetry}
              className="mt-3 inline-flex min-h-11 items-center gap-2 rounded-lg px-3 text-sm font-medium text-primary hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <RefreshCw size={15} aria-hidden="true" />
              Retry
            </button>
          </div>
        ) : sessions.length === 0 ? (
          <div className="px-4 py-10 text-center">
            <MessageSquare className="mx-auto mb-3 text-muted-foreground" size={26} aria-hidden="true" />
            <p className="text-sm font-medium text-foreground">No conversations yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Start a new chat to ask about this dataset.
            </p>
          </div>
        ) : (
          <ul className="space-y-1">
            {sessions.map((session) => {
              const active = activeSessionId === session.id;
              return (
                <li key={session.id}>
                  <div
                    className={`group flex min-h-14 items-center gap-1 rounded-lg border ${
                      active
                        ? "border-primary/20 bg-primary/10"
                        : "border-transparent hover:bg-accent"
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => onSelect(session)}
                      disabled={deletingId === session.id || busy}
                      aria-current={active ? "true" : undefined}
                      className="flex min-w-0 flex-1 items-center gap-3 rounded-lg px-3 py-2.5 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary disabled:opacity-50"
                    >
                      <MessageSquare
                        size={17}
                        className={`shrink-0 ${active ? "text-primary" : "text-muted-foreground"}`}
                        aria-hidden="true"
                      />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-medium text-foreground">
                          {session.title}
                        </span>
                        {session.last_message && (
                          <span className="mt-1 block truncate text-xs text-muted-foreground">
                            {session.last_message}
                          </span>
                        )}
                        <span className="mt-1 block text-xs text-muted-foreground">
                          {formatSessionDate(session.updated_at)}
                        </span>
                      </span>
                    </button>
                    <button
                      type="button"
                      aria-label={`Delete conversation ${session.title}`}
                      title="Delete conversation"
                      disabled={deletingId === session.id || busy}
                      onClick={() => onDelete(session)}
                      className="mr-1 flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition hover:bg-destructive/10 hover:text-destructive focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50 lg:opacity-0 lg:group-hover:opacity-100 lg:focus-visible:opacity-100"
                    >
                      {deletingId === session.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                      ) : (
                        <Trash2 size={16} aria-hidden="true" />
                      )}
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

export default function AIChatPage() {
  const { datasetId: routeDatasetId } = useParams<{ datasetId?: string }>();
  const parsedRouteDatasetId = routeDatasetId ? Number(routeDatasetId) : null;

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | "">("");
  const [datasetsLoading, setDatasetsLoading] = useState(true);
  const [datasetsError, setDatasetsError] = useState("");

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [sessionsError, setSessionsError] = useState("");
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);
  const [loadingSessionId, setLoadingSessionId] = useState<number | null>(null);
  const [sessionLoadError, setSessionLoadError] = useState("");
  const [failedSession, setFailedSession] = useState<ChatSession | null>(null);
  const [creatingSession, setCreatingSession] = useState(false);
  const [deletingSessionId, setDeletingSessionId] = useState<number | null>(null);
  const [mobileHistoryOpen, setMobileHistoryOpen] = useState(false);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [upgradeRequired, setUpgradeRequired] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messageListRef = useRef<HTMLDivElement>(null);
  const historyTriggerRef = useRef<HTMLButtonElement>(null);
  const historyDialogRef = useRef<HTMLElement>(null);
  const historyWasOpenRef = useRef(false);
  const sendingRef = useRef(false);
  const creatingRef = useRef(false);
  const sessionRequestRef = useRef(0);
  const selectedDatasetRef = useRef<number | "">("");
  const activeSessionRef = useRef<number | null>(null);
  const forceScrollRef = useRef(false);
  const nearBottomRef = useRef(true);

  const focusComposer = useCallback(() => {
    requestAnimationFrame(() => textareaRef.current?.focus());
  }, []);

  const loadAllDatasets = useCallback(async () => {
    setDatasetsLoading(true);
    setDatasetsError("");
    try {
      const firstPage = await getDatasets({ page: 1, page_size: 100 });
      const allDatasets = [...firstPage.items];
      for (let page = 2; page <= firstPage.pages; page += 1) {
        const nextPage = await getDatasets({ page, page_size: 100 });
        allDatasets.push(...nextPage.items);
      }
      setDatasets(allDatasets);

      if (parsedRouteDatasetId !== null) {
        if (
          !Number.isSafeInteger(parsedRouteDatasetId) ||
          parsedRouteDatasetId < 1 ||
          !allDatasets.some((dataset) => dataset.id === parsedRouteDatasetId)
        ) {
          setSelectedDatasetId("");
          selectedDatasetRef.current = "";
          setDatasetsError("The dataset in this link could not be found.");
          return;
        }
        setSelectedDatasetId(parsedRouteDatasetId);
        selectedDatasetRef.current = parsedRouteDatasetId;
      } else if (allDatasets.length > 0) {
        setSelectedDatasetId((current) => {
          const existing = allDatasets.some((dataset) => dataset.id === current);
          const next = existing ? current : allDatasets[0].id;
          selectedDatasetRef.current = next;
          return next;
        });
      } else {
        setSelectedDatasetId("");
        selectedDatasetRef.current = "";
      }
    } catch (loadError) {
      setDatasetsError(
        getChatErrorMessage(loadError, "Unable to load your datasets. Please try again.")
      );
    } finally {
      setDatasetsLoading(false);
    }
  }, [parsedRouteDatasetId]);

  useEffect(() => {
    void loadAllDatasets();
  }, [loadAllDatasets]);

  const loadSessionMessages = useCallback(async (session: ChatSession) => {
    const requestId = ++sessionRequestRef.current;
    setLoadingSessionId(session.id);
    setSessionLoadError("");
    setFailedSession(null);

    try {
      const result = await getChatSession(session.id);
      if (
        requestId !== sessionRequestRef.current ||
        selectedDatasetRef.current !== result.dataset_id
      ) {
        return;
      }
      setSelectedDatasetId(result.dataset_id);
      selectedDatasetRef.current = result.dataset_id;
      setSelectedSessionId(session.id);
      activeSessionRef.current = session.id;
      setMessages(result.messages);
      forceScrollRef.current = true;
      setError("");
      setUpgradeRequired(false);
      setMobileHistoryOpen(false);
    } catch (loadError) {
      if (requestId !== sessionRequestRef.current) return;
      setSessionLoadError(
        getChatErrorMessage(loadError, "Unable to load this conversation. Please try again.")
      );
      setFailedSession(session);
    } finally {
      if (requestId === sessionRequestRef.current) {
        setLoadingSessionId(null);
      }
    }
  }, []);

  const loadSessions = useCallback(async (datasetId: number) => {
    setSessionsLoading(true);
    setSessionsError("");
    try {
      const result = await getChatSessions(datasetId);
      setSessions(result);
      const current = result.find(
        (session) => session.id === activeSessionRef.current
      );
      const next = current ?? result[0];

      if (next) {
        await loadSessionMessages(next);
      } else {
        activeSessionRef.current = null;
        setSelectedSessionId(null);
        setMessages([]);
        setLoadingSessionId(null);
        setSessionLoadError("");
      }
    } catch (loadError) {
      setSessionsError(
        getChatErrorMessage(loadError, "Unable to load chat history. Please try again.")
      );
    } finally {
      setSessionsLoading(false);
    }
  }, [loadSessionMessages]);

  useEffect(() => {
    const id = selectedDatasetId;
    if (typeof id !== "number") {
      sessionRequestRef.current += 1;
      activeSessionRef.current = null;
      setSessions([]);
      setMessages([]);
      setSelectedSessionId(null);
      setLoadingSessionId(null);
      setSessionLoadError("");
      return;
    }

    activeSessionRef.current = null;
    setSessions([]);
    setMessages([]);
    setSelectedSessionId(null);
    setSessionLoadError("");
    void loadSessions(id);
  }, [selectedDatasetId, loadSessions]);

  useEffect(() => {
    function handleEscape(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape" && mobileHistoryOpen) {
        setMobileHistoryOpen(false);
        historyTriggerRef.current?.focus();
      }
      if (event.key === "Tab" && mobileHistoryOpen && historyDialogRef.current) {
        const focusable = historyDialogRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], select:not([disabled]), textarea:not([disabled])'
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    }
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [mobileHistoryOpen]);

  useEffect(() => {
    if (mobileHistoryOpen) {
      historyWasOpenRef.current = true;
      requestAnimationFrame(() => historyDialogRef.current?.focus());
    } else if (historyWasOpenRef.current) {
      historyWasOpenRef.current = false;
      historyTriggerRef.current?.focus();
    }
  }, [mobileHistoryOpen]);

  useEffect(() => {
    const element = messageListRef.current;
    if (!element) return;

    const frame = requestAnimationFrame(() => {
      if (forceScrollRef.current || nearBottomRef.current) {
        element.scrollTop = element.scrollHeight;
      }
      forceScrollRef.current = false;
    });
    return () => cancelAnimationFrame(frame);
  }, [messages, sending, loadingSessionId]);

  function handleMessageScroll() {
    const element = messageListRef.current;
    if (!element) return;
    nearBottomRef.current =
      element.scrollHeight - element.scrollTop - element.clientHeight < 120;
  }

  async function handleCreateChat() {
    if (
      typeof selectedDatasetId !== "number" ||
      creatingRef.current ||
      sendingRef.current ||
      loadingSessionId !== null
    ) {
      return;
    }

    creatingRef.current = true;
    setCreatingSession(true);
    setError("");
    setUpgradeRequired(false);
    try {
      const session = await createChatSession(selectedDatasetId);
      setSessions((current) => [
        session,
        ...current.filter((item) => item.id !== session.id),
      ]);
      setSelectedSessionId(session.id);
      activeSessionRef.current = session.id;
      setMessages([]);
      setSessionLoadError("");
      setFailedSession(null);
      setMobileHistoryOpen(false);
      forceScrollRef.current = true;
      focusComposer();
    } catch (createError) {
      setError(
        getChatErrorMessage(createError, "Unable to create a new conversation. Please try again.")
      );
      setUpgradeRequired(isPlanRestrictionError(createError));
    } finally {
      creatingRef.current = false;
      setCreatingSession(false);
    }
  }

  async function handleDeleteChat(session: ChatSession) {
    if (
      deletingSessionId !== null ||
      sendingRef.current ||
      loadingSessionId !== null
    ) return;
    if (!window.confirm(`Delete "${session.title}" and its messages? This cannot be undone.`)) {
      return;
    }

    setDeletingSessionId(session.id);
    setError("");
    try {
      await deleteChatSession(session.id);
      const remaining = sessions.filter((item) => item.id !== session.id);
      setSessions(remaining);

      if (activeSessionRef.current === session.id) {
        activeSessionRef.current = null;
        setSelectedSessionId(null);
        setMessages([]);
        setSessionLoadError("");
        if (remaining[0]) {
          await loadSessionMessages(remaining[0]);
        }
      }
    } catch (deleteError) {
      setError(
        getChatErrorMessage(deleteError, "Unable to delete this conversation. Please try again.")
      );
    } finally {
      setDeletingSessionId(null);
    }
  }

  async function handleRetrySession() {
    if (failedSession) await loadSessionMessages(failedSession);
  }

  async function handleSend(customMessage?: string) {
    const question = (customMessage ?? message).trim();
    if (!question || sendingRef.current || loadingSessionId !== null) return;

    if (typeof selectedDatasetId !== "number") {
      setError("You need a dataset before starting an analysis chat.");
      return;
    }

    sendingRef.current = true;
    setSending(true);
    setError("");
    setUpgradeRequired(false);
    let sessionId = selectedSessionId;

    try {
      if (sessionId === null) {
        const session = await createChatSession(selectedDatasetId);
        sessionId = session.id;
        setSessions((current) => [session, ...current]);
        setSelectedSessionId(session.id);
        activeSessionRef.current = session.id;
      }

      const optimisticMessage: ChatMessage = {
        role: "user",
        content: question,
      };
      forceScrollRef.current = true;
      setMessages((current) => [...current, optimisticMessage]);

      const response = await sendChatMessage(
        selectedDatasetId,
        sessionId,
        question
      );
      if (!response.answer.trim()) {
        throw new Error("The assistant returned an empty response.");
      }

      setMessages(response.messages);
      setMessage("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
        textareaRef.current.style.overflowY = "hidden";
      }
      forceScrollRef.current = true;
      focusComposer();

      try {
        const updatedSessions = await getChatSessions(selectedDatasetId);
        setSessions(updatedSessions);
        const active = updatedSessions.find((item) => item.id === sessionId);
        if (active) setSelectedSessionId(active.id);
        setSessionsError("");
      } catch (historyError) {
        setSessionsError(
          getChatErrorMessage(historyError, "Message sent, but chat history could not be refreshed.")
        );
      }
    } catch (sendError) {
      setError(
        getChatErrorMessage(sendError, "Failed to get a response from InsightForge AI.")
      );
      setUpgradeRequired(isPlanRestrictionError(sendError));
      if (sessionId !== null) {
        try {
          const current = await getChatSession(sessionId);
          setMessages(current.messages);
        } catch {
          // Keep the current view and the unsent draft if the refresh also fails.
        }
      }
    } finally {
      sendingRef.current = false;
      setSending(false);
    }
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void handleSend();
    }
  }

  function handleComposerChange(value: string) {
    setMessage(value);
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
    textarea.style.overflowY = textarea.scrollHeight > 160 ? "auto" : "hidden";
  }

  function handleDatasetChange(value: string) {
    const next = value ? Number(value) : "";
    sessionRequestRef.current += 1;
    activeSessionRef.current = null;
    selectedDatasetRef.current = next;
    setSelectedDatasetId(next);
    setSelectedSessionId(null);
    setSessions([]);
    setMessages([]);
    setSessionLoadError("");
    setError("");
    setUpgradeRequired(false);
  }

  function chooseSuggestion(prompt: string) {
    setMessage(prompt);
    focusComposer();
  }

  const activeSession = sessions.find(
    (session) => session.id === selectedSessionId
  );
  const isPlanError = upgradeRequired || isPlanRestrictionError(error);
  const historyPanelProps: HistoryPanelProps = {
    sessions,
    activeSessionId: selectedSessionId,
    loading: sessionsLoading,
    creating: creatingSession,
    deletingId: deletingSessionId,
    error: sessionsError,
    canCreate: typeof selectedDatasetId === "number",
    onCreate: () => void handleCreateChat(),
    onSelect: (session) => void loadSessionMessages(session),
    onDelete: (session) => void handleDeleteChat(session),
    onRetry: () => {
      if (typeof selectedDatasetId === "number") {
        void loadSessions(selectedDatasetId);
      }
    },
    busy: sending || loadingSessionId !== null,
  };

  return (
    <section className="flex h-[calc(100dvh-6.5rem)] min-h-[24rem] min-w-0 flex-col overflow-hidden rounded-xl border border-border bg-background shadow-sm sm:h-[calc(100dvh-7rem)] md:h-[calc(100dvh-8rem)]">
      <div className="flex min-h-0 flex-1">
        <aside className="hidden w-64 shrink-0 border-r border-border lg:block xl:w-72">
          <HistoryPanel {...historyPanelProps} />
        </aside>

        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <header className="flex min-h-16 flex-wrap items-center gap-3 border-b border-border bg-card px-3 py-2.5 sm:px-5">
            <button
              type="button"
              onClick={() => setMobileHistoryOpen(true)}
              ref={historyTriggerRef}
              aria-label="Open chat history"
              className="flex h-11 shrink-0 items-center gap-2 rounded-lg border border-border px-3 text-sm font-medium text-foreground hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary lg:hidden"
            >
              <PanelLeft size={18} aria-hidden="true" />
              <span className="hidden min-[360px]:inline">History</span>
            </button>

            <div className="min-w-0 flex-1">
              <label htmlFor="chat-dataset" className="sr-only">
                Dataset for this conversation
              </label>
              <select
                id="chat-dataset"
                value={selectedDatasetId}
                onChange={(event) => handleDatasetChange(event.target.value)}
                disabled={
                  datasetsLoading ||
                  datasets.length === 0 ||
                  sending ||
                  loadingSessionId !== null
                }
                className="block min-h-11 w-full min-w-0 max-w-xl truncate rounded-lg border border-border bg-background px-3 text-sm text-foreground outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-60 sm:px-4"
              >
                {datasetsLoading ? (
                  <option value="">Loading datasets...</option>
                ) : datasets.length === 0 ? (
                  <option value="">No datasets available</option>
                ) : (
                  <>
                    <option value="">Choose a dataset</option>
                    {datasets.map((dataset) => (
                      <option key={dataset.id} value={dataset.id}>
                        {dataset.original_filename}
                      </option>
                    ))}
                  </>
                )}
              </select>
            </div>

            <div className="hidden min-w-0 max-w-[30%] text-right sm:block">
              <p className="truncate text-sm font-semibold text-foreground">
                {activeSession?.title ?? "New conversation"}
              </p>
              <p className="text-xs text-muted-foreground">
                {datasets.find((dataset) => dataset.id === selectedDatasetId)?.original_filename ?? "Dataset chat"}
              </p>
            </div>
          </header>

          {datasetsError && (
            <div role="alert" className="flex items-center justify-between gap-3 border-b border-border bg-destructive/5 px-4 py-3 text-sm text-destructive">
              <span>{datasetsError}</span>
              <button
                type="button"
                onClick={() => void loadAllDatasets()}
                className="inline-flex min-h-11 shrink-0 items-center gap-2 rounded-lg px-3 font-medium hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              >
                <RefreshCw size={15} aria-hidden="true" />
                Retry
              </button>
            </div>
          )}

          {error && (
            <div role="alert" className="flex flex-wrap items-center gap-x-2 gap-y-1 border-b border-border bg-destructive/5 px-4 py-3 text-sm text-destructive">
              <span>{error}</span>
              {isPlanError && <PlanUpgradeLink className="font-medium underline" />}
            </div>
          )}

          <div
            ref={messageListRef}
            onScroll={handleMessageScroll}
            role="log"
            aria-label="Conversation messages"
            aria-live="polite"
            aria-relevant="additions text"
            className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 py-5 sm:px-6 sm:py-7"
          >
            {loadingSessionId !== null ? (
              <div className="flex h-full min-h-40 items-center justify-center">
                <div role="status" className="flex items-center gap-3 text-sm text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" aria-hidden="true" />
                  Loading conversation...
                </div>
              </div>
            ) : datasetsLoading ? (
              <div role="status" className="flex h-full items-center justify-center text-sm text-muted-foreground">
                Loading your datasets...
              </div>
            ) : datasets.length === 0 ? (
              <div className="flex h-full min-h-56 flex-col items-center justify-center px-4 text-center">
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                  <Bot size={27} aria-hidden="true" />
                </div>
                <h2 className="text-lg font-semibold text-foreground">
                  Upload a dataset to start chatting
                </h2>
                <p className="mt-2 max-w-sm text-sm leading-6 text-muted-foreground">
                  InsightForge AI uses your dataset analysis to answer questions about its contents.
                </p>
                <Link
                  to="/dashboard/upload"
                  className="mt-5 inline-flex min-h-11 items-center justify-center rounded-lg bg-primary px-4 py-2.5 font-medium text-primary-foreground hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                >
                  Upload dataset
                </Link>
              </div>
            ) : (
              <>
                {sessionLoadError && (
                  <div className="mx-auto mb-4 flex w-full max-w-4xl flex-wrap items-center justify-between gap-3 rounded-lg border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm">
                    <p role="alert" className="text-destructive">
                      {sessionLoadError}
                    </p>
                    <button
                      type="button"
                      onClick={() => void handleRetrySession()}
                      className="inline-flex min-h-11 shrink-0 items-center gap-2 rounded-lg px-3 font-medium text-primary hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                    >
                      <RefreshCw size={15} aria-hidden="true" />
                      Retry
                    </button>
                  </div>
                )}
                {messages.length === 0 ? (
              <div className="flex min-h-full flex-col items-center justify-center py-3">
                <div className="w-full max-w-2xl px-1 text-center">
                  <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-sm">
                    <Sparkles size={25} aria-hidden="true" />
                  </div>
                  <h2 className="text-xl font-semibold text-foreground sm:text-2xl">
                    What would you like to know?
                  </h2>
                  <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-muted-foreground">
                    Ask a question about{" "}
                    <span className="font-medium text-foreground">
                      {datasets.find((dataset) => dataset.id === selectedDatasetId)?.original_filename}
                    </span>
                    . Your conversation is saved to your account.
                  </p>
                  <div className="mt-6 flex flex-wrap justify-center gap-2">
                    {SUGGESTED_PROMPTS.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => chooseSuggestion(prompt)}
                        disabled={sending}
                        className="min-h-11 max-w-full rounded-full border border-border bg-card px-3.5 py-2 text-left text-sm text-foreground transition hover:border-primary/40 hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50 sm:px-4"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="mx-auto flex w-full max-w-4xl flex-col gap-5 pb-3 sm:gap-7">
                {messages.map((chatMessage, index) => {
                  const isUser = chatMessage.role === "user";
                  return (
                    <article
                      key={chatMessage.id ?? `${chatMessage.role}-${index}`}
                      className={`flex min-w-0 items-start gap-2.5 sm:gap-3 ${
                        isUser ? "justify-end" : "justify-start"
                      }`}
                    >
                      {!isUser && (
                        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground sm:h-10 sm:w-10">
                          <Bot size={19} aria-hidden="true" />
                        </div>
                      )}
                      <div
                        className={`min-w-0 max-w-[88%] rounded-2xl px-4 py-3 sm:max-w-[82%] sm:px-5 sm:py-4 ${
                          isUser
                            ? "rounded-br-md bg-primary text-primary-foreground"
                            : "rounded-bl-md border border-border bg-card text-foreground shadow-sm"
                        }`}
                      >
                        <p className="whitespace-pre-wrap text-[15px] leading-7 [overflow-wrap:anywhere]">
                          {chatMessage.content}
                        </p>
                      </div>
                      {isUser && (
                        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-muted text-foreground sm:h-10 sm:w-10">
                          <User size={18} aria-hidden="true" />
                        </div>
                      )}
                    </article>
                  );
                })}
                {sending && (
                  <div className="flex items-start gap-3" role="status">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground sm:h-10 sm:w-10">
                      <Bot size={19} aria-hidden="true" />
                    </div>
                    <div className="flex items-center gap-3 rounded-2xl rounded-bl-md border border-border bg-card px-4 py-3 text-sm text-muted-foreground shadow-sm">
                      <span className="flex gap-1" aria-hidden="true">
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary [animation-delay:150ms]" />
                        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary [animation-delay:300ms]" />
                      </span>
                      InsightForge AI is thinking...
                    </div>
                  </div>
                )}
              </div>
                )}
              </>
            )}
          </div>

          <footer className="shrink-0 border-t border-border bg-card px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 sm:px-5 sm:pt-4">
            <div className="mx-auto w-full max-w-4xl">
              <label htmlFor="chat-composer" className="sr-only">
                Message InsightForge AI
              </label>
              <div className="flex items-end gap-2 rounded-2xl border border-border bg-background p-2 shadow-sm transition focus-within:border-primary/60 focus-within:ring-2 focus-within:ring-primary/15 sm:gap-3 sm:p-2.5">
                <textarea
                  id="chat-composer"
                  ref={textareaRef}
                  rows={1}
                  value={message}
                  onChange={(event) => handleComposerChange(event.target.value)}
                  onKeyDown={handleComposerKeyDown}
                  disabled={
                    sending ||
                    loadingSessionId !== null ||
                    typeof selectedDatasetId !== "number"
                  }
                  placeholder={
                    typeof selectedDatasetId === "number"
                      ? "Ask anything about your dataset..."
                      : "Choose a dataset to start chatting"
                  }
                  className="max-h-40 min-h-12 min-w-0 flex-1 resize-none overflow-y-hidden bg-transparent px-2 py-3 text-base leading-6 text-foreground outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-60 sm:px-3"
                />
                <button
                  type="button"
                  onClick={() => void handleSend()}
                  disabled={
                    sending ||
                    loadingSessionId !== null ||
                    !message.trim() ||
                    typeof selectedDatasetId !== "number"
                  }
                  aria-label={sending ? "Sending message" : "Send message"}
                  className="flex h-12 shrink-0 items-center justify-center gap-2 rounded-xl bg-primary px-3 font-medium text-primary-foreground transition hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 sm:px-5"
                >
                  {sending ? (
                    <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
                  ) : (
                    <Send size={18} aria-hidden="true" />
                  )}
                  <span className="hidden sm:inline">{sending ? "Sending" : "Send"}</span>
                </button>
              </div>
              <p className="mt-2 hidden text-center text-xs text-muted-foreground sm:block">
                Enter to send · Shift + Enter for a new line
              </p>
            </div>
          </footer>
        </div>
      </div>

      {mobileHistoryOpen && (
        <div className="fixed inset-x-0 bottom-0 top-20 z-50 lg:hidden" role="presentation">
          <button
            type="button"
            aria-label="Close chat history"
            onClick={() => setMobileHistoryOpen(false)}
            className="absolute inset-0 h-full w-full bg-black/40"
          />
          <aside
            role="dialog"
            ref={historyDialogRef}
            tabIndex={-1}
            aria-modal="true"
            aria-label="Chat history"
            className="absolute inset-y-0 left-0 w-[min(21rem,calc(100vw-2.5rem))] border-r border-border bg-card shadow-xl"
          >
            <HistoryPanel
              {...historyPanelProps}
              onClose={() => setMobileHistoryOpen(false)}
            />
          </aside>
        </div>
      )}
    </section>
  );
}
