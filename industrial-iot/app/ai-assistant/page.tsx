"use client";

import { useMemo, useState } from "react";
import { Activity, Bot, Database, LineChart, Send, User } from "lucide-react";
import { Bar, Line } from "react-chartjs-2";
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
  payload?: ChatResponse;
};

type TrendPoint = {
  timestamp: string;
  avg: number;
  min: number;
  max: number;
  count: number;
};

type SensorSummary = {
  sensor: string;
  samples: number;
  avg: number;
  peak: number;
  min: number;
};

type Anomaly = {
  sensor: string;
  unit: string;
  value: number;
  min: number;
  max: number;
  timestamp: string;
  severity: string;
};

type ChatResponse = {
  answer: string;
  source: string;
  status: string;
  intent: string;
  context: {
    query?: string;
    table?: string;
    machine_id?: string;
    sensor?: string;
    window?: string;
  };
  data?: {
    sensor?: string;
    value?: number;
    unit?: string;
    timestamp?: string;
    trend_data?: TrendPoint[];
    sensors?: SensorSummary[];
    anomalies?: Anomaly[];
    anomalies_count?: number;
  };
};

const QUICK_PROMPTS = [
  "What is the latest vibration reading?",
  "Show temperature trend for the last day.",
  "Any anomalies in the last week?",
  "Give me a machine health summary.",
];

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
  const [input, setInput] = useState("Give me a machine health summary from the database.");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [source, setSource] = useState<string>("database");

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  async function askAssistant() {
    if (!canSend) return;

    const userText = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setInput("");
    setLoading(true);

    try {
      const response = await chatApi.query(userText);
      const data = response.data as ChatResponse;
      setSource(data.source);
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer, payload: data }]);
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

  function askQuickPrompt(prompt: string) {
    if (loading) return;
    setInput(prompt);
  }

  return (
    <div className="space-y-6 pb-6">
      <Card className="border-cyan-500/20 bg-[radial-gradient(circle_at_10%_10%,rgba(34,211,238,0.2),transparent_45%),radial-gradient(circle_at_90%_20%,rgba(16,185,129,0.2),transparent_45%),linear-gradient(135deg,rgba(15,23,42,0.95),rgba(2,6,23,0.98))]">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold text-white">PredictX AI Assistant</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-300">
              Ask operational questions and get answers strictly from your database. Trend charts and sensor summaries shown below are rendered from returned SQL results.
            </p>
          </div>
          <Badge className="border-emerald-500/30 bg-emerald-500/15 text-emerald-300">
            Source: {source}
          </Badge>
        </div>
      </Card>

      <Card>
        <p className="mb-2 text-sm text-slate-400">Ask anything about current machine health and telemetry.</p>
        <div className="mb-3 flex flex-wrap gap-2">
          {QUICK_PROMPTS.map((prompt) => (
            <Button
              key={prompt}
              type="button"
              variant="outline"
              size="sm"
              className="border-slate-700 bg-slate-900/40 text-slate-200 hover:bg-slate-800"
              onClick={() => askQuickPrompt(prompt)}
            >
              {prompt}
            </Button>
          ))}
        </div>
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
                  "rounded-xl border p-4 text-sm",
                  message.role === "user"
                    ? "border-cyan-500/30 bg-cyan-500/10 text-cyan-100"
                    : "border-slate-700 bg-slate-900/70 text-slate-200",
                )}
              >
                <p className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  {message.role === "user" ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
                  {message.role}
                </p>
                <p>{message.content}</p>
                {message.role === "assistant" && message.payload ? (
                  <div className="mt-4 space-y-4 border-t border-slate-700/80 pt-4">
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <Badge className="border-cyan-500/30 bg-cyan-500/10 text-cyan-200">
                        <Database className="mr-1 h-3 w-3" />
                        {message.payload.context?.table ?? "database"}
                      </Badge>
                      <Badge className="border-slate-600 bg-slate-800/70 text-slate-200">
                        intent: {message.payload.intent}
                      </Badge>
                      <Badge
                        className={cn(
                          "border",
                          message.payload.status === "success"
                            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
                            : message.payload.status === "no_data"
                              ? "border-amber-500/30 bg-amber-500/10 text-amber-200"
                              : "border-red-500/30 bg-red-500/10 text-red-200",
                        )}
                      >
                        status: {message.payload.status}
                      </Badge>
                    </div>
                    <ChatDataPanels payload={message.payload} />
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function ChatDataPanels({ payload }: { payload: ChatResponse }) {
  const trendData = payload.data?.trend_data ?? [];
  const summarySensors = payload.data?.sensors ?? [];
  const anomalies = payload.data?.anomalies ?? [];

  if (trendData.length > 0) {
    const labels = trendData.map((point) => point.timestamp.slice(11, 16));

    return (
      <div className="space-y-2">
        <p className="flex items-center gap-2 text-sm font-medium text-slate-200">
          <LineChart className="h-4 w-4 text-cyan-300" />
          Trend from SQL time buckets
        </p>
        <div className="rounded-xl border border-slate-700/80 bg-slate-950/60 p-3">
          <Line
            data={{
              labels,
              datasets: [
                {
                  label: "Average",
                  data: trendData.map((point) => point.avg),
                  borderColor: "#22d3ee",
                  backgroundColor: "rgba(34, 211, 238, 0.15)",
                  fill: true,
                  tension: 0.3,
                },
                {
                  label: "Max",
                  data: trendData.map((point) => point.max),
                  borderColor: "#fb7185",
                  backgroundColor: "rgba(251, 113, 133, 0)",
                  fill: false,
                  tension: 0.25,
                },
              ],
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: { legend: { display: true, labels: { color: "#cbd5e1" } } },
              scales: {
                x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.12)" } },
                y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.12)" } },
              },
            }}
            height={220}
          />
        </div>
      </div>
    );
  }

  if (summarySensors.length > 0) {
    return (
      <div className="space-y-2">
        <p className="flex items-center gap-2 text-sm font-medium text-slate-200">
          <Activity className="h-4 w-4 text-emerald-300" />
          7-day sensor averages from aggregates
        </p>
        <div className="rounded-xl border border-slate-700/80 bg-slate-950/60 p-3">
          <Bar
            data={{
              labels: summarySensors.map((sensor) => sensor.sensor),
              datasets: [
                {
                  label: "Average value",
                  data: summarySensors.map((sensor) => sensor.avg),
                  backgroundColor: ["#22d3ee", "#34d399", "#f59e0b"],
                  borderRadius: 6,
                },
              ],
            }}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: { legend: { display: false } },
              scales: {
                x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.12)" } },
                y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.12)" } },
              },
            }}
            height={220}
          />
        </div>
      </div>
    );
  }

  if (anomalies.length > 0) {
    return (
      <div className="space-y-2">
        <p className="text-sm font-medium text-rose-200">Anomalies from sensor aggregates</p>
        <div className="space-y-2 rounded-xl border border-slate-700/80 bg-slate-950/60 p-3">
          {anomalies.slice(0, 5).map((anomaly, index) => (
            <div key={`${anomaly.sensor}-${anomaly.timestamp}-${index}`} className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-xs">
              <span className="text-slate-200">
                {anomaly.sensor} · {anomaly.value} {anomaly.unit}
              </span>
              <Badge className="border-rose-500/40 bg-rose-500/15 text-rose-300">{anomaly.severity}</Badge>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (typeof payload.data?.value === "number") {
    return (
      <div className="rounded-xl border border-slate-700/80 bg-slate-950/60 p-3">
        <p className="text-xs uppercase tracking-wide text-slate-400">Latest reading</p>
        <p className="mt-1 text-xl font-semibold text-white">
          {payload.data.value} {payload.data.unit ?? ""}
        </p>
        <p className="mt-1 text-xs text-slate-500">timestamp: {payload.data.timestamp ?? "n/a"}</p>
      </div>
    );
  }

  return (
    <p className="text-xs text-slate-500">
      No chartable data was returned for this response.
    </p>
  );
}
