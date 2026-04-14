"use client";

import { useQuery } from "@tanstack/react-query";
import { alerts, machineTwins, predictionRisks, sensors } from "@/lib/mock-data";
import { analyticsApi, machineApi, predictionApi, sensorApi } from "@/services/api";

export function useSensorTelemetry() {
  return useQuery({
    queryKey: ["sensor-live"],
    queryFn: async () => {
      try {
        const response = await sensorApi.live();
        return response.data;
      } catch {
        return sensors;
      }
    },
    refetchInterval: 5000,
  });
}

export function usePredictions() {
  return useQuery({
    queryKey: ["predictions"],
    queryFn: async () => {
      try {
        const response = await predictionApi.failure();
        return response.data;
      } catch {
        return predictionRisks;
      }
    },
    refetchInterval: 10000,
  });
}

export function usePredictiveAlerts() {
  return useQuery({
    queryKey: ["predictive-alerts"],
    queryFn: async () => {
      try {
        const response = await predictionApi.alerts();
        return response.data.activeAlerts ?? response.data;
      } catch {
        return alerts;
      }
    },
  });
}

export function useMachines() {
  return useQuery({
    queryKey: ["machines"],
    queryFn: async () => {
      try {
        const response = await machineApi.list();
        return response.data;
      } catch {
        return machineTwins.slice(0, 1);
      }
    },
    refetchInterval: 8000,
  });
}

export function useAnalytics() {
  return useQuery({
    queryKey: ["analytics"],
    queryFn: async () => {
      try {
        const response = await analyticsApi.summary();
        return response.data;
      } catch {
        return {
          uptimeTrend: [97.8, 98.0, 98.1, 98.2, 98.3, 98.1, 98.2],
          temperatureTrend: [63, 64, 65, 66, 67, 68, 67],
          vibrationTrend: [2.9, 3.1, 3.3, 3.5, 3.8, 4.0, 4.1],
          downtimeCauses: [42, 24, 18, 16],
          costTrend: [18, 20, 19, 24, 22, 26, 25],
          sensorNoise: [5, 7, 8, 12, 18, 15, 10, 7, 4],
          summary: {
            uptime: 98.2,
            alerts: 2,
            avgTemperature: 67,
            failureProbability: 43,
          },
        };
      }
    },
  });
}
