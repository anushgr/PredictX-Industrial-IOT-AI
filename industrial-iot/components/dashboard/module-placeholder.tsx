import { Card } from "@/components/ui/card";

export function ModulePlaceholder({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <Card>
      <h1 className="text-2xl font-semibold text-white">{title}</h1>
      <p className="mt-2 text-slate-300">{description}</p>
      <p className="mt-4 text-sm text-slate-500">
        This module is scaffolded for API integration and enterprise workflows.
      </p>
    </Card>
  );
}
