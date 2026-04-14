"use client";

import { useMemo, useState } from "react";
import type { AlertRecord } from "@/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { severityClasses } from "@/lib/utils";

const PAGE_SIZE = 4;

export function AlertTable({ rows }: { rows: AlertRecord[] }) {
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    return rows.filter((row) => {
      const passSeverity = severityFilter === "all" || row.severity === severityFilter;
      const text = `${row.machine} ${row.alertType} ${row.sensor}`.toLowerCase();
      const passQuery = text.includes(query.toLowerCase());
      return passSeverity && passQuery;
    });
  }, [rows, severityFilter, query]);

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const current = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <Card>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-white">Alerts Center</h3>
        <div className="flex w-full flex-wrap gap-2 md:w-auto">
          <Select value={severityFilter} onValueChange={setSeverityFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Severity" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All severities</SelectItem>
              <SelectItem value="Critical">Critical</SelectItem>
              <SelectItem value="High">High</SelectItem>
              <SelectItem value="Medium">Medium</SelectItem>
              <SelectItem value="Low">Low</SelectItem>
            </SelectContent>
          </Select>
          <Input type="date" className="w-40" />
          <Input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
            placeholder="Search machine"
            className="w-44"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left text-slate-400">
              {[
                "Time",
                "Machine",
                "Alert Type",
                "Severity",
                "Sensor Source",
                "Predicted Cause",
                "Status",
                "Action",
              ].map((head) => (
                <th key={head} className="px-2 py-3 font-medium">
                  {head}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {current.map((row) => (
              <tr key={row.id} className="border-b border-slate-900/80 hover:bg-slate-900/70">
                <td className="px-2 py-3 text-slate-300">{row.time}</td>
                <td className="px-2 py-3 text-slate-200">{row.machine}</td>
                <td className="px-2 py-3 text-slate-300">{row.alertType}</td>
                <td className="px-2 py-3">
                  <Badge className={severityClasses[row.severity]}>{row.severity}</Badge>
                </td>
                <td className="px-2 py-3 text-slate-300">{row.sensor}</td>
                <td className="px-2 py-3 text-slate-300">{row.predictedCause}</td>
                <td className="px-2 py-3 text-slate-300">{row.status}</td>
                <td className="px-2 py-3">
                  <div className="flex gap-1">
                    <Button variant="outline" size="sm">
                      Acknowledge
                    </Button>
                    <Button variant="secondary" size="sm">
                      Assign Engineer
                    </Button>
                    <Button variant="ghost" size="sm">
                      Resolve
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
        <p>
          Showing {(page - 1) * PAGE_SIZE + 1} -
          {Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length}
        </p>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Prev
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={page === pages}
            onClick={() => setPage((p) => Math.min(pages, p + 1))}
          >
            Next
          </Button>
        </div>
      </div>
    </Card>
  );
}
