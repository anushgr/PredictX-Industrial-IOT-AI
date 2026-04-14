import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const insights = [
  {
    id: "insight-1",
    title: "Repeated vibration bursts before overload",
    confidence: "91%",
    detail:
      "Pattern detected in 14 historical events where harmonic spikes preceded overload within a 25 minute window.",
  },
  {
    id: "insight-2",
    title: "Temperature rises 17 mins before failure",
    confidence: "88%",
    detail:
      "Gradient change over baseline exceeded dynamic threshold in 83% of motor failure incidents.",
  },
  {
    id: "insight-3",
    title: "Machine 12 deviates from historical baseline by 34%",
    confidence: "94%",
    detail:
      "Multivariate drift in vibration and thermal signatures indicates high probability of bearing instability.",
  },
];

export function InsightsAccordion() {
  return (
    <Card>
      <h3 className="text-lg font-semibold text-white">AI Insights</h3>
      <Accordion type="single" collapsible className="mt-4 space-y-2">
        {insights.map((insight) => (
          <AccordionItem
            key={insight.id}
            value={insight.id}
            className="rounded-xl border border-slate-800 bg-slate-950/60"
          >
            <AccordionTrigger>
              <span className="text-sm">{insight.title}</span>
            </AccordionTrigger>
            <AccordionContent>
              <p className="text-slate-300">{insight.detail}</p>
              <p className="mt-2 text-xs text-cyan-300">Confidence: {insight.confidence}</p>
              <Button variant="outline" size="sm" className="mt-3">
                Learn More
              </Button>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </Card>
  );
}
