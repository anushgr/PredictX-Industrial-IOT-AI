export type MachineHealth = "Healthy" | "Warning" | "Critical";

export interface KpiMetric {
  title: string;
  value: string;
  delta: string;
  series: number[];
  icon: string;
  tone: "success" | "warning" | "danger" | "info";
}

export interface SensorReading {
  id: string;
  name: string;
  unit: string;
  value: number;
  threshold: number;
  anomalyCount: number;
  series: number[];
}

export interface MachineTwin {
  id: string;
  name: string;
  status: MachineHealth;
  rpm: number;
  temperature: number;
  vibration: number;
  failureProbability: number;
  lastMaintenance: string;
}

export interface PredictionRisk {
  label: string;
  value: number;
}

export interface AlertRecord {
  id: string;
  time: string;
  machine: string;
  alertType: string;
  severity: "Critical" | "High" | "Medium" | "Low";
  sensor: string;
  predictedCause: string;
  status: "Open" | "Assigned" | "Resolved";
}

export interface UserRecord {
  id: string;
  name: string;
  email: string;
  role: "Admin" | "Maintenance Engineer" | "Operator" | "Viewer";
  lastLogin: string;
  accessLevel: string;
  status: "Active" | "Invited" | "Suspended";
}
