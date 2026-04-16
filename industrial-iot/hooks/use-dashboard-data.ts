"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi, machineApi, predictionApi, sensorApi } from "@/services/api";

type SensorScore = {
  score?: number;
  classification?: string;
  health_pct?: number;
  confidence?: number;
};

export type PredictionSnapshotPayload = {
  machine_id?: string;
  timestamp?: string;
  sensor_scores?: Record<string, SensorScore>;
  machine_health?: {
    overall_health_pct?: number;
    status?: string;
    worst_sensor?: string;
    estimated_rul_hours?: number;
    recommendation?: string;
    overall_anomaly_score?: number;
  };
};

export type PredictionTrendPoint = {
  timeLabel: string;
  confidence: number;
  anomalyScore: number;
};

export type PredictionSnapshotWithTrend = PredictionSnapshotPayload & {
  trend: PredictionTrendPoint[];
};

const MAX_TREND_POINTS = 20;
let predictionTrendBuffer: PredictionTrendPoint[] = [];

type PredictionItem = {
  sensor?: string;
  label?: string;
  failureProbability?: number;
  value?: number;
  predictionScore?: number;
};

export function useSensorTelemetry() {
  return useQuery({
    queryKey: ["sensor-live"],
    queryFn: async () => {
      const response = await sensorApi.live();
      return response.data;
    },
    refetchInterval: 5000,
  });
}

export function usePredictions() {
  return useQuery({
    queryKey: ["predictions"],
    queryFn: async () => {
      const response = await predictionApi.failure();
      const payload = response.data;
      const rawPredictions = Array.isArray(payload)
        ? payload
        : Array.isArray(payload?.predictions)
          ? payload.predictions
          : [];

      return rawPredictions.map((item: PredictionItem) => {
        const sensorName = String(item?.sensor ?? item?.label ?? "sensor");
        const percent = Number(
          item?.failureProbability ??
            item?.value ??
            Math.round(Number(item?.predictionScore ?? 0) * 100),
        );

        return {
          label: sensorName.charAt(0).toUpperCase() + sensorName.slice(1),
          value: Number.isFinite(percent) ? percent : 0,
        };
      });
    },
    refetchInterval: 10000,
  });
}

export function usePredictionSnapshot() {
  return useQuery({
    queryKey: ["prediction-snapshot"],
    queryFn: async () => {
      const response = await predictionApi.failure();
      const payload = response.data as PredictionSnapshotPayload;

      const sensorScores = payload?.sensor_scores ?? {};
      const confidenceValues = Object.values(sensorScores)
        .map((score) => Number(score?.confidence ?? 0))
        .filter((value) => Number.isFinite(value));

      const avgConfidence = confidenceValues.length
        ? confidenceValues.reduce((acc, value) => acc + value, 0) / confidenceValues.length
        : 0;

      const anomalyScore = Number(payload?.machine_health?.overall_anomaly_score ?? 0);
      const timestamp = payload?.timestamp ? new Date(payload.timestamp) : new Date();
      const timeLabel = timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

      predictionTrendBuffer = [
        ...predictionTrendBuffer,
        {
          timeLabel,
          confidence: Number((avgConfidence * 100).toFixed(2)),
          anomalyScore: Number((anomalyScore * 100).toFixed(2)),
        },
      ].slice(-MAX_TREND_POINTS);

      return {
        ...payload,
        trend: predictionTrendBuffer,
      } as PredictionSnapshotWithTrend;
    },
    refetchInterval: 2000,
  });
}

export function usePredictiveAlerts() {
  return useQuery({
    queryKey: ["predictive-alerts"],
    queryFn: async () => {
      const response = await predictionApi.alerts();
      return response.data.activeAlerts ?? response.data;
    },
  });
}

export function useMachines() {
  return useQuery({
    queryKey: ["machines"],
    queryFn: async () => {
      const response = await machineApi.list();
      return response.data;
    },
    refetchInterval: 8000,
  });
}

export function useAnalytics() {
  return useQuery({
    queryKey: ["analytics"],
    queryFn: async () => {
      const response = await analyticsApi.summary();
      return response.data;
    },
  });
}
