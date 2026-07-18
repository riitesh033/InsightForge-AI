import { useState } from "react";
import {
  Send,
  Bot,
  User,
  Sparkles,
} from "lucide-react";

export default function AIChatPage() {
  const [message, setMessage] = useState("");

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">

      {/* Header */}
      <div className="mb-6">

        <h1 className="text-3xl font-bold text-foreground">
          AI Chat
        </h1>

        <p className="mt-2 text-muted-foreground">
          Ask questions about your uploaded datasets using natural language.
        </p>

      </div>

      {/* Chat Container */}
      <div className="flex flex-1 flex-col overflow-hidden rounded-xl border border-border bg-card shadow-sm">

        {/* Messages */}
        <div className="flex-1 space-y-6 overflow-y-auto p-6">

          {/* AI Message */}
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

                <br /><br />

                Upload a dataset and ask me anything.

                <br /><br />

                Examples:

                <br />

                • Summarize my dataset

                <br />

                • Show missing values

                <br />

                • Detect outliers

                <br />

                • Explain feature importance

                <br />

                • Recommend data cleaning steps

              </p>

            </div>

          </div>

          {/* User Example */}
          <div className="flex justify-end">

            <div className="flex max-w-xl items-start gap-4">

              <div className="rounded-xl bg-primary p-4 text-primary-foreground">

                How many missing values are there?

              </div>

              <div className="rounded-full bg-muted p-3">
                <User size={20} />
              </div>

            </div>

          </div>

        </div>

        {/* Input */}
        <div className="border-t border-border bg-background p-5">

          <div className="flex gap-4">

            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
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
              "
            />

            <button
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
              "
            >
              <Send size={18} />

              Send

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