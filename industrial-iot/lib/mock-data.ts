import type {
  AlertRecord,
  KpiMetric,
  MachineTwin,
  PredictionRisk,
  SensorReading,
  UserRecord,
} from "@/types";

export const kpis: KpiMetric[] = [
  {
    title: "Machine Uptime",
    value: "98.2%",
    delta: "+0.6% this week",
    series: [95, 96, 97, 97.4, 98.1, 98.2, 98.2],
    icon: "Gauge",
    tone: "success",
  },
  {
    title: "Active Alerts",
    value: "17",
    delta: "4 critical",
    series: [10, 13, 9, 11, 17, 15, 17],
    icon: "BellRing",
    tone: "danger",
  },
  {
    title: "Avg Temperature",
    value: "67C",
    delta: "-1.1C vs yesterday",
    series: [71, 70, 69, 68, 67.5, 67, 67],
    icon: "Thermometer",
    tone: "warning",
  },
  {
    title: "Failure Probability Avg",
    value: "21%",
    delta: "Within acceptable range",
    series: [24, 23, 26, 21, 19, 22, 21],
    icon: "ShieldAlert",
    tone: "info",
  },
];

export const sensors: SensorReading[] = [
  {
    id: "sound",
    name: "Sound Sensor",
    unit: "dB",
    value: 72,
    threshold: 4,
    anomalyCount: 3,
    series: [63, 65, 67, 66, 70, 72, 71, 69, 73, 72],
  },
  {
    id: "vibration",
    name: "Vibration Sensor",
    unit: "mm/s",
    value: 4.1,
    threshold: 10,
    anomalyCount: 5,
    series: [2.7, 3.1, 3.3, 3.6, 3.8, 4, 4.1, 4.3, 4.2, 4.1],
  },
  {
    id: "temp",
    name: "Temperature Sensor",
    unit: "C",
    value: 67,
    threshold: 30,
    anomalyCount: 2,
    series: [59, 61, 62, 63, 64, 66, 67, 68, 67, 67],
  },
];

export const machineTwins: MachineTwin[] = [
  {
    id: "m-01",
    name: "Lathe-01",
    status: "Healthy",
    rpm: 1450,
    temperature: 64,
    vibration: 2.7,
    failureProbability: 12,
    lastMaintenance: "2026-04-01",
  },
  {
    id: "m-07",
    name: "Conveyor-07",
    status: "Warning",
    rpm: 1022,
    temperature: 71,
    vibration: 4.1,
    failureProbability: 43,
    lastMaintenance: "2026-03-22",
  },
  {
    id: "m-12",
    name: "Press-12",
    status: "Critical",
    rpm: 890,
    temperature: 78,
    vibration: 5.2,
    failureProbability: 82,
    lastMaintenance: "2026-02-17",
  },
  {
    id: "m-09",
    name: "Mixer-09",
    status: "Healthy",
    rpm: 1310,
    temperature: 63,
    vibration: 2.9,
    failureProbability: 17,
    lastMaintenance: "2026-03-27",
  },
  {
    id: "m-16",
    name: "CNC-16",
    status: "Warning",
    rpm: 1180,
    temperature: 69,
    vibration: 3.8,
    failureProbability: 37,
    lastMaintenance: "2026-03-10",
  },
  {
    id: "m-21",
    name: "Boiler-21",
    status: "Critical",
    rpm: 760,
    temperature: 81,
    vibration: 5.7,
    failureProbability: 88,
    lastMaintenance: "2026-02-04",
  },
];

export const predictionRisks: PredictionRisk[] = [
  { label: "Bearing Wear Risk", value: 82 },
  { label: "Overheat Risk", value: 33 },
  { label: "Shaft Misalignment", value: 57 },
  { label: "Motor Failure", value: 19 },
];

export const alerts: AlertRecord[] = [
  {
    id: "a-1",
    time: "10:18",
    machine: "Machine 07",
    alertType: "Vibration Spike",
    severity: "Critical",
    sensor: "Vibration",
    predictedCause: "Bearing wear acceleration",
    status: "Open",
  },
  {
    id: "a-2",
    time: "09:55",
    machine: "Machine 12",
    alertType: "Overheat",
    severity: "High",
    sensor: "Temperature",
    predictedCause: "Cooling valve drift",
    status: "Assigned",
  },
  {
    id: "a-3",
    time: "09:11",
    machine: "Machine 03",
    alertType: "Acoustic anomaly",
    severity: "Medium",
    sensor: "Sound",
    predictedCause: "Cavitation onset",
    status: "Open",
  },
  {
    id: "a-4",
    time: "08:47",
    machine: "Machine 09",
    alertType: "Transient vibration",
    severity: "Low",
    sensor: "Vibration",
    predictedCause: "Loose fastener",
    status: "Resolved",
  },
];

export const users: UserRecord[] = [
  {
    id: "u1",
    name: "Ava Thompson",
    email: "ava@predictx.ai",
    role: "Admin",
    lastLogin: "2026-04-14 09:20",
    accessLevel: "Global",
    status: "Active",
  },
  {
    id: "u2",
    name: "Rohan Patel",
    email: "rohan@predictx.ai",
    role: "Maintenance Engineer",
    lastLogin: "2026-04-14 08:41",
    accessLevel: "Plant A",
    status: "Active",
  },
  {
    id: "u3",
    name: "Ethan Cole",
    email: "ethan@predictx.ai",
    role: "Operator",
    lastLogin: "2026-04-13 19:22",
    accessLevel: "Line 4",
    status: "Invited",
  },
  {
    id: "u4",
    name: "Sana Malik",
    email: "sana@predictx.ai",
    role: "Viewer",
    lastLogin: "2026-04-12 16:10",
    accessLevel: "Analytics",
    status: "Suspended",
  },
];

export const tempTrend = {
  labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  machineA: [62, 63, 64, 64, 65, 66, 65],
  machineB: [66, 67, 68, 67, 68, 70, 69],
  machineC: [58, 60, 61, 62, 63, 64, 63],
};

export const failureForecast = [14, 18, 22, 19, 26, 30, 27];

export const downtimeCauses = [28, 22, 16, 12, 22];

export const maintenanceCost = [18, 20, 17, 24, 26, 21, 23];

export const sensorNoise = [5, 9, 12, 17, 19, 14, 11, 8, 4];
