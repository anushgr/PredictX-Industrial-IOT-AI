import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const reports = [
  "Daily Plant Report",
  "Weekly Failure Forecast",
  "Monthly Maintenance Summary",
  "Energy Usage Report",
];

export function ReportsModule() {
  return (
    <Card>
      <h3 className="text-lg font-semibold text-white">Reports Module</h3>
      <div className="mt-4 space-y-3">
        {reports.map((report) => (
          <div
            key={report}
            className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900/70 p-3"
          >
            <p className="text-sm text-slate-200">{report}</p>
            <div className="flex gap-2">
              <Button size="sm" variant="outline">
                PDF
              </Button>
              <Button size="sm" variant="secondary">
                Excel
              </Button>
              <Button size="sm" variant="ghost">
                CSV
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
