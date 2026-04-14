"use client";

import { motion } from "framer-motion";
import { BellRing, Gauge, ShieldAlert, Thermometer } from "lucide-react";
import { Line } from "react-chartjs-2";
import { Card } from "@/components/ui/card";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const iconMap = {
  Gauge,
  BellRing,
  Thermometer,
  ShieldAlert,
};

interface StatCardProps {
  title: string;
  value: string;
  delta: string;
  series: number[];
  icon: keyof typeof iconMap;
}

export function StatCard({ title, value, delta, series, icon }: StatCardProps) {
  const Icon = iconMap[icon];

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <motion.div whileHover={{ y: -4 }} transition={{ duration: 0.2 }}>
          <Card className="h-full">
            <div className="mb-3 flex items-start justify-between">
              <p className="text-sm text-slate-400">{title}</p>
              <Icon className="h-5 w-5 text-cyan-300" />
            </div>
            <p className="text-3xl font-semibold text-white">{value}</p>
            <p className="mt-1 text-xs text-slate-400">{delta}</p>
            <div className="mt-3 h-14">
              <Line
                data={{
                  labels: series.map((_, idx) => idx + 1),
                  datasets: [
                    {
                      data: series,
                      borderColor: "#22d3ee",
                      backgroundColor: "rgba(34,211,238,0.18)",
                      fill: true,
                      tension: 0.35,
                      borderWidth: 2,
                      pointRadius: 0,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false }, tooltip: { enabled: false } },
                  scales: {
                    x: { display: false },
                    y: { display: false },
                  },
                }}
              />
            </div>
          </Card>
        </motion.div>
      </TooltipTrigger>
      <TooltipContent>Live KPI tracked from the last 7 polling windows.</TooltipContent>
    </Tooltip>
  );
}
