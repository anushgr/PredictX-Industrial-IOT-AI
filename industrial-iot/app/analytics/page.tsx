"use client";

import { Activity, Gauge, Thermometer } from "lucide-react";
import { Bar, Line, Pie } from "react-chartjs-2";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAnalytics } from "@/hooks/use-dashboard-data";

export default function AnalyticsPage() {
  const { data, isLoading } = useAnalytics();

  if (isLoading || !data) {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        <Skeleton className="h-72" />
        <Skeleton className="h-72" />
        <Skeleton className="h-72 lg:col-span-2" />
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-6">
      <Card className="border-cyan-500/20 bg-gradient-to-r from-slate-900 via-slate-900/95 to-cyan-950/20">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-slate-400">Analytics for Conveyor-07</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Operational analytics</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-300">
              Backend dummy JSON drives this page. It summarizes uptime, temperature, vibration, downtime causes, and maintenance cost for the single monitored machine.
            </p>
          </div>
          <Badge className="border-emerald-500/30 bg-emerald-500/15 text-emerald-300">
            Backend analytics ready
          </Badge>
        </div>
      </Card>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { title: "Uptime", value: `${data.summary.uptime}%`, icon: Gauge },
          { title: "Alerts", value: `${data.summary.alerts}`, icon: Activity },
          { title: "Avg Temp", value: `${data.summary.avgTemperature}C`, icon: Thermometer },
          { title: "Failure Risk", value: `${data.summary.failureProbability}%`, icon: Activity },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.title} className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">{item.title}</p>
                <p className="mt-1 text-2xl font-semibold text-white">{item.value}</p>
              </div>
              <Icon className="h-5 w-5 text-cyan-300" />
            </Card>
          );
        })}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="mb-4 text-lg font-semibold text-white">Uptime and temperature trend</h2>
          <div className="h-72">
            <Line
              data={{
                labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                datasets: [
                  {
                    label: "Uptime %",
                    data: data.uptimeTrend,
                    borderColor: "#22d3ee",
                    backgroundColor: "rgba(34,211,238,0.15)",
                    fill: true,
                    tension: 0.35,
                  },
                  {
                    label: "Temperature C",
                    data: data.temperatureTrend,
                    borderColor: "#f59e0b",
                    backgroundColor: "rgba(245,158,11,0.15)",
                    fill: false,
                    tension: 0.35,
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: "#cbd5e1" } } },
                scales: {
                  x: { ticks: { color: "#64748b" }, grid: { color: "rgba(51,65,85,0.25)" } },
                  y: { ticks: { color: "#64748b" }, grid: { color: "rgba(51,65,85,0.25)" } },
                },
              }}
            />
          </div>
        </Card>

        <Card>
          <h2 className="mb-4 text-lg font-semibold text-white">Vibration trend</h2>
          <div className="h-72">
            <Line
              data={{
                labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                datasets: [
                  {
                    label: "RMS vibration",
                    data: data.vibrationTrend,
                    borderColor: "#fb7185",
                    backgroundColor: "rgba(251,113,133,0.15)",
                    fill: true,
                    tension: 0.35,
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: "#cbd5e1" } } },
                scales: {
                  x: { ticks: { color: "#64748b" }, grid: { color: "rgba(51,65,85,0.25)" } },
                  y: { ticks: { color: "#64748b" }, grid: { color: "rgba(51,65,85,0.25)" } },
                },
              }}
            />
          </div>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card>
          <h2 className="mb-4 text-lg font-semibold text-white">Downtime causes</h2>
          <div className="h-64">
            <Pie
              data={{
                labels: ["Mechanical", "Electrical", "Cooling", "Other"],
                datasets: [
                  {
                    data: data.downtimeCauses,
                    backgroundColor: ["#22d3ee", "#f59e0b", "#ef4444", "#64748b"],
                  },
                ],
              }}
              options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: "#cbd5e1" } } } }}
            />
          </div>
        </Card>

        <Card>
          <h2 className="mb-4 text-lg font-semibold text-white">Maintenance cost trend</h2>
          <div className="h-64">
            <Bar
              data={{
                labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                datasets: [
                  {
                    label: "Cost k$",
                    data: data.costTrend,
                    backgroundColor: "rgba(56,189,248,0.7)",
                    borderRadius: 10,
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: "#cbd5e1" } } },
                scales: {
                  x: { ticks: { color: "#64748b" }, grid: { display: false } },
                  y: { ticks: { color: "#64748b" }, grid: { color: "rgba(51,65,85,0.25)" } },
                },
              }}
            />
          </div>
        </Card>

        <Card>
          <h2 className="mb-4 text-lg font-semibold text-white">Sensor noise distribution</h2>
          <div className="h-64">
            <Bar
              data={{
                labels: ["0-5", "5-10", "10-15", "15-20", "20-25", "25-30", "30-35", "35-40", "40-45"],
                datasets: [
                  {
                    label: "Noise",
                    data: data.sensorNoise,
                    backgroundColor: "rgba(34,197,94,0.65)",
                    borderRadius: 10,
                  },
                ],
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: "#cbd5e1" } } },
                scales: {
                  x: { ticks: { color: "#64748b" }, grid: { display: false } },
                  y: { ticks: { color: "#64748b" }, grid: { color: "rgba(51,65,85,0.25)" } },
                },
              }}
            />
          </div>
        </Card>
      </section>

      <Card className="border-amber-500/30 bg-amber-500/10 text-amber-100">
        Current analytics indicate vibration is the leading early-warning signal. Focus maintenance action on Conveyor-07 bearing inspection and thermal clearance checks.
      </Card>
    </div>
  );
}
