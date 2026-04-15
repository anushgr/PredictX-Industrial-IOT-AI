"use client";

import { useMemo, useState } from "react";
import { Send } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TextareaHTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { chatApi } from "@/services/api";
import { toast } from "sonner";

type ChatMsg = {
  role: "user" | "assistant";
  content: string;
};

function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={cn(
        "min-h-28 w-full rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500",
        props.className,
      )}
    />
  );
}

export default function AIAssistantPage() {
  const [input, setInput] = useState("Give me a quick status summary and next action for Conveyor-07.");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [source, setSource] = useState<string>("unknown");

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  async function askAssistant() {
    if (!canSend) return;

    const userText = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setInput("");
    setLoading(true);

    try {
      const response = await chatApi.query(userText);
      const data = response.data as {
        answer: string;
        source: string;
      };
      setSource(data.source);
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
    } catch {
      toast.error("Assistant request failed. Check backend token/session.");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Assistant is temporarily unavailable. Please retry after backend is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 pb-6">
      <Card className="border-cyan-500/20 bg-gradient-to-r from-slate-900 via-slate-900/95 to-cyan-950/20">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold text-white">PredictX AI Assistant</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-300">
              Basic NIM chatbot setup is enabled. It can answer using real-time machine and sensor context from backend APIs. More advanced features will be added with database integration.
            </p>
          </div>
          <Badge className="border-emerald-500/30 bg-emerald-500/15 text-emerald-300">
            Source: {source}
          </Badge>
        </div>
      </Card>

      <Card>
        <p className="mb-2 text-sm text-slate-400">Ask anything about current machine health and telemetry.</p>
        <Textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Type your operational question..."
        />
        <div className="mt-3 flex justify-end">
          <Button onClick={askAssistant} disabled={!canSend}>
            {loading ? "Querying..." : "Ask Assistant"}
            <Send className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </Card>

      <Card>
        <h2 className="mb-3 text-lg font-semibold text-white">Conversation</h2>
        {messages.length === 0 ? (
          <p className="text-sm text-slate-400">No messages yet. Ask your first question above.</p>
        ) : (
          <div className="space-y-3">
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={cn(
                  "rounded-xl border p-3 text-sm",
                  message.role === "user"
                    ? "border-cyan-500/30 bg-cyan-500/10 text-cyan-100"
                    : "border-slate-700 bg-slate-900/70 text-slate-200",
                )}
              >
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  {message.role}
                </p>
                <p>{message.content}</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
