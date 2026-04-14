"use client";

import { motion } from "framer-motion";
import type { MachineTwin } from "@/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const statusMap = {
  Healthy: "bg-emerald-400",
  Warning: "bg-amber-400",
  Critical: "bg-red-400",
};

export function MachineCard({ machine }: { machine: MachineTwin }) {
  return (
    <motion.div whileHover={{ y: -4 }} transition={{ duration: 0.2 }}>
      <Card className="h-full">
        <div className="mb-3 flex items-center justify-between">
          <h4 className="text-base font-semibold text-white">{machine.name}</h4>
          <div className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${statusMap[machine.status]}`} />
            <span className="text-xs text-slate-400">{machine.status}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <p className="text-slate-400">RPM</p>
          <p className="text-right text-slate-200">{machine.rpm}</p>
          <p className="text-slate-400">Temp</p>
          <p className="text-right text-slate-200">{machine.temperature}C</p>
          <p className="text-slate-400">Vibration</p>
          <p className="text-right text-slate-200">{machine.vibration} mm/s</p>
          <p className="text-slate-400">Failure chance</p>
          <p className="text-right text-red-300">{machine.failureProbability}%</p>
        </div>

        <Badge className="mt-3 border-slate-700 text-slate-300">
          Last maintenance: {machine.lastMaintenance}
        </Badge>

        <div className="mt-4 grid grid-cols-3 gap-2">
          <Button size="sm" variant="secondary">
            View Details
          </Button>
          <Button size="sm" variant="outline">
            Diagnostics
          </Button>
          <Button size="sm" variant="ghost">
            History
          </Button>
        </div>
      </Card>
    </motion.div>
  );
}
