"use client";

import { Card } from "@/components/ui/card";
import { MachineCard } from "@/components/dashboard/machine-card";
import { useMachines } from "@/hooks/use-dashboard-data";

export default function MachinesPage() {
  const { data: machines = [] } = useMachines();

  return (
    <div className="space-y-6 pb-6">
      <Card>
        <h1 className="text-2xl font-semibold text-white">Machines</h1>
        <p className="mt-2 text-sm text-slate-300">
          Only Conveyor-07 is being tracked for now, with live status, RPM, temperature, vibration, and predicted failure chance.
        </p>
      </Card>
      <div className="grid gap-4 lg:grid-cols-2">
        {machines.map((machine) => (
          <MachineCard key={machine.id} machine={machine} />
        ))}
      </div>
    </div>
  );
}
