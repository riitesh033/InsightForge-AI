import { useEffect, useState } from "react";
import {
  Send,
  Bot,
  User,
  Sparkles,
} from "lucide-react";

import {
  Dataset,
  getDatasets,
} from "@/services/dataset";

import api from "@/services/api";

interface ChatMessage {
  id?: number;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}

interface ChatResponse {
  session_id: number;
  dataset_id: number;
  answer: string;
  messages: ChatMessage[];
}

export default function AIChatPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] =
    useState<number | "">("");

  const [message, setMessage] = useState("");

  const [messages, setMessages] =
    useState<ChatMessage[]>([]);

  const [loadingDatasets, setLoadingDatasets] =
    useState(true);

  const [sending, setSending] =
    useState(false);

  const [error, setError] =
    useState("");


  /* =========================
     Load Datasets
  ========================== */

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
        setSelectedDatasetId(
          response.items[0].id
        );
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


  /* =========================
     Send Message
  ========================== */

  async function sendMessage(
    customMessage?: string
  ) {
    const question =
      customMessage ?? message;

    if (!question.trim()) {
      return;
    }

    if (!selectedDatasetId) {
      setError(
        "Please select a dataset first."
      );

      return;
    }

    try {
      setSending(true);
      setError("");

      const userMessage: ChatMessage = {
        role: "user",
        content: question.trim(),
      };

      setMessages((previous) => [
        ...previous,
        userMessage,
      ]);

      setMessage("");

      const response =
        await api.post<ChatResponse>(
          `/chat/${selectedDatasetId}`,
          {
            message: question.trim(),
          }
        );

      setMessages(
        response.data.messages
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


  /* =========================
     Suggested Prompt
  ========================== */

  function handleSuggestion(
    prompt: string
  ) {
    sendMessage(prompt);
  }


  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">

      {/* Header */}

      <div className="mb-6">

        <h1 className="text-3xl font-bold text-foreground">
          AI Chat
        </h1>

        <p className="mt-2 text-muted-foreground">
          Ask questions about your uploaded
          datasets using natural language.
        </p>

      </div>


      {/* Dataset Selector */}

      <div className="mb-4">

        <label className="mb-2 block text-sm font-medium text-foreground">
          Select Dataset
        </label>

        <select
          value={selectedDatasetId}
          onChange={(e) => {
            setSelectedDatasetId(
              e.target.value
                ? Number(e.target.value)
                : ""
            );

            setMessages([]);
            setError("");
          }}
          disabled={
            loadingDatasets ||
            datasets.length === 0
          }
          className="w-full max-w-xl rounded-lg border border-border bg-card px-4 py-3 text-foreground outline-none focus:border-primary"
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
            datasets.map((dataset) => (
              <option
                key={dataset.id}
                value={dataset.id}
              >
                {dataset.original_filename}
              </option>
            ))
          )}

        </select>

      </div>


      {/* Error */}

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600 dark:border-red-900 dark:bg-red-950 dark:text-red-400">
          {error}
        </div>
      )}


      {/* Chat Container */}

      <div className="flex flex-1 flex-col overflow-hidden rounded-xl border border-border bg-card shadow-sm">

        {/* Messages */}

        <div className="flex-1 space-y-6 overflow-y-auto p-6">

          {/* Welcome Message */}

          {messages.length === 0 && (
            <div className="flex items-start gap-4">

              <div className="rounded-full bg-primary p-3 text-primary-foreground">
                <Bot size={20} />
              </div>

              <div className="max-w-2xl rounded-xl bg-muted p-4">

                <p className="font-semibold text-foreground">
                  InsightForge AI
                </p>

                <p className="mt-2 text-muted-foreground">
                  👋 Welcome!
                  <br />
                  <br />
                  Select a dataset and ask me
                  anything about it.
                  <br />
                  <br />
                  I can help you understand
                  missing values, duplicates,
                  correlations, outliers,
                  statistics, and data quality.
                </p>

              </div>

            </div>
          )}


          {/* Conversation */}

          {messages.map((chatMessage, index) => {

            const isUser =
              chatMessage.role === "user";

            return (
              <div
                key={
                  chatMessage.id ??
                  `${chatMessage.role}-${index}`
                }
                className={
                  isUser
                    ? "flex justify-end"
                    : "flex items-start gap-4"
                }
              >

                {!isUser && (
                  <div className="rounded-full bg-primary p-3 text-primary-foreground">
                    <Bot size={20} />
                  </div>
                )}

                <div
                  className={
                    isUser
                      ? "flex max-w-xl items-start gap-4"
                      : "max-w-2xl rounded-xl bg-muted p-4"
                  }
                >

                  <div
                    className={
                      isUser
                        ? "rounded-xl bg-primary p-4 text-primary-foreground"
                        : ""
                    }
                  >
                    {chatMessage.content}
                  </div>

                  {isUser && (
                    <div className="rounded-full bg-muted p-3 text-foreground">
                      <User size={20} />
                    </div>
                  )}

                </div>

              </div>
            );
          })}


          {/* Loading */}

          {sending && (
            <div className="flex items-start gap-4">

              <div className="rounded-full bg-primary p-3 text-primary-foreground">
                <Bot size={20} />
              </div>

              <div className="rounded-xl bg-muted p-4 text-muted-foreground">
                Thinking...
              </div>

            </div>
          )}

        </div>


        {/* Input */}

        <div className="border-t border-border bg-background p-5">

          <div className="flex gap-4">

            <input
              value={message}
              onChange={(e) =>
                setMessage(e.target.value)
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
              disabled={sending}
              placeholder="Ask InsightForge AI..."
              className="
                flex-1
                rounded-lg
                border
                border-border
                bg-card
                px-4
                py-3
                text-foreground
                placeholder:text-muted-foreground
                focus:border-primary
                focus:outline-none
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
                !selectedDatasetId
              }
              className="
                flex
                items-center
                gap-2
                rounded-lg
                bg-primary
                px-6
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

      </div>


      {/* Suggestions */}

      <div className="mt-6 rounded-xl border border-border bg-card p-6">

        <div className="mb-5 flex items-center gap-2">

          <Sparkles
            className="text-primary"
            size={20}
          />

          <h2 className="text-lg font-semibold text-foreground">
            Suggested Prompts
          </h2>

        </div>

        <div className="flex flex-wrap gap-3">

          {[
            "Summarize my dataset",
            "Detect missing values",
            "Find duplicate rows",
            "Show correlations",
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
                !selectedDatasetId
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