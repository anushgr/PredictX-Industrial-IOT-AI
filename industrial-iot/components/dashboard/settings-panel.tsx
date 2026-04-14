"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";

export function SettingsPanel() {
  return (
    <Card>
      <h1 className="text-xl font-semibold text-white">Settings</h1>
      <Tabs defaultValue="general" className="mt-4">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="ai">AI Model</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="mt-4 space-y-3">
          <Input placeholder="Plant name" defaultValue="Plant A" />
          <Input placeholder="Timezone" defaultValue="Asia/Kolkata" />
          <Input placeholder="Branding" defaultValue="PredictX Industrial AI" />
        </TabsContent>

        <TabsContent value="alerts" className="mt-4 space-y-4">
          <Input placeholder="Temperature threshold" defaultValue="75" />
          <div className="flex items-center justify-between rounded-xl border border-slate-800 p-3">
            <p className="text-sm text-slate-300">SMS Alerts</p>
            <Switch defaultChecked />
          </div>
          <div className="flex items-center justify-between rounded-xl border border-slate-800 p-3">
            <p className="text-sm text-slate-300">Email Alerts</p>
            <Switch defaultChecked />
          </div>
        </TabsContent>

        <TabsContent value="ai" className="mt-4 space-y-3">
          <Input placeholder="Retrain schedule" defaultValue="Daily at 02:00" />
          <Input placeholder="Confidence threshold" defaultValue="85" />
        </TabsContent>

        <TabsContent value="security" className="mt-4 space-y-4">
          <div className="flex items-center justify-between rounded-xl border border-slate-800 p-3">
            <p className="text-sm text-slate-300">MFA</p>
            <Switch defaultChecked />
          </div>
          <Input placeholder="Device auth certificates" defaultValue="Enabled" />
        </TabsContent>
      </Tabs>

      <Button className="mt-5">Save Configuration</Button>
    </Card>
  );
}
