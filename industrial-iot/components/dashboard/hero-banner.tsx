"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Download, FileBarChart2, PlusCircle, Stethoscope } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

function AnimatedNumber({ value }: { value: number }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    const duration = 850;
    const start = performance.now();
    let frame = 0;

    const update = (time: number) => {
      const progress = Math.min((time - start) / duration, 1);
      setDisplay(Math.floor(progress * value));
      if (progress < 1) frame = requestAnimationFrame(update);
    };

    frame = requestAnimationFrame(update);
    return () => cancelAnimationFrame(frame);
  }, [value]);

  return <span>{display}</span>;
}

export function HeroBanner() {
  return (
    <Card className="overflow-hidden bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/40">
      <div className="grid gap-5 lg:grid-cols-[1.2fr_1fr_auto]">
        <div>
          <p className="text-sm text-slate-400">Plant Status Overview</p>
          <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-3">
              <p className="text-xs text-slate-500">Total Machines</p>
              <p className="text-xl font-semibold text-white">
                <AnimatedNumber value={128} />
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-3">
              <p className="text-xs text-slate-500">Healthy</p>
              <p className="text-xl font-semibold text-emerald-300">
                <AnimatedNumber value={111} />
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-3">
              <p className="text-xs text-slate-500">Warning</p>
              <p className="text-xl font-semibold text-amber-300">
                <AnimatedNumber value={11} />
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-3">
              <p className="text-xs text-slate-500">Critical</p>
              <p className="text-xl font-semibold text-red-300">
                <AnimatedNumber value={6} />
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-cyan-900/70 bg-cyan-950/20 p-4">
          <p className="text-sm text-slate-300">AI Engine Status</p>
          <div className="mt-3 space-y-2 text-sm">
            <p className="text-emerald-300">Model Active</p>
            <p className="text-slate-300">Last Trained: 2 hours ago</p>
            <p className="text-slate-200">Accuracy: 94.8%</p>
          </div>
          <Badge className="mt-3 border-emerald-500/30 bg-emerald-500/15 text-emerald-300">
            Inference Pipeline Healthy
          </Badge>
        </div>

        <motion.div
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          className="grid grid-cols-2 gap-2 lg:w-[220px]"
        >
          <Button variant="secondary" size="sm">
            <FileBarChart2 className="mr-2 h-4 w-4" />
            Generate Report
          </Button>
          <Button variant="outline" size="sm">
            <PlusCircle className="mr-2 h-4 w-4" />
            Add Machine
          </Button>
          <Button variant="secondary" size="sm">
            <Stethoscope className="mr-2 h-4 w-4" />
            Trigger Diagnostic
          </Button>
          <Button variant="outline" size="sm">
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
        </motion.div>
      </div>
    </Card>
  );
}
