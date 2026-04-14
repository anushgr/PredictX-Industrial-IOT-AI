"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { AlertCircle, ArrowRight, LockKeyhole, Mail } from "lucide-react";
import { toast } from "sonner";
import { authApi } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("ava@predictx.ai");
  const [password, setPassword] = useState("admin123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await authApi.login(email, password);
      const token = response.data.access_token;
      localStorage.setItem("predictx_token", token);
      toast.success("JWT token received from backend");
      router.replace("/");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Login failed";
      setError(message);
      toast.error("Invalid credentials or API unavailable");
    } finally {
      setLoading(false);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid min-h-screen place-items-center px-4 py-10"
    >
      <Card className="w-full max-w-6xl overflow-hidden border-slate-800 bg-slate-950/70 p-0 shadow-2xl shadow-cyan-950/20">
        <div className="grid lg:grid-cols-[1.1fr_0.9fr]">
          <div className="relative overflow-hidden border-b border-slate-800 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.18),_transparent_40%),linear-gradient(180deg,#07111f_0%,#020617_100%)] p-8 lg:border-b-0 lg:border-r">
            <Badge className="border-cyan-400/30 bg-cyan-400/10 text-cyan-300">
              PredictX Industrial AI
            </Badge>
            <h1 className="mt-6 max-w-xl text-4xl font-semibold tracking-tight text-white md:text-5xl">
              Industrial failure intelligence with secure JWT access.
            </h1>
            <p className="mt-4 max-w-xl text-sm leading-6 text-slate-300 md:text-base">
              Sign in to the predictive maintenance cockpit, receive a JWT from FastAPI, and
              unlock live telemetry, alarms, machine twins, and AI model recommendations.
            </p>

            <div className="mt-8 grid gap-3 text-sm text-slate-300 sm:grid-cols-2">
              {[
                "FastAPI auth with bearer token transfer",
                "Real-time telemetry and prediction APIs",
                "Role-based industrial control center",
                "Production-ready enterprise UI",
              ].map((item) => (
                <div key={item} className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
                  {item}
                </div>
              ))}
            </div>

            <div className="mt-10 rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-4 text-sm text-cyan-100">
              Demo credentials: ava@predictx.ai / admin123
            </div>
          </div>

          <div className="p-8 lg:p-10">
            <div className="mb-8">
              <p className="text-sm text-slate-400">Secure Sign In</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">Access the dashboard</h2>
            </div>

            <form className="space-y-4" onSubmit={handleSubmit}>
              <label className="block space-y-2">
                <span className="text-sm text-slate-300">Email</span>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                  <Input
                    type="email"
                    className="pl-9"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="name@company.com"
                  />
                </div>
              </label>

              <label className="block space-y-2">
                <span className="text-sm text-slate-300">Password</span>
                <div className="relative">
                  <LockKeyhole className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                  <Input
                    type="password"
                    className="pl-9"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Enter password"
                  />
                </div>
              </label>

              {error && (
                <div className="flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">
                  <AlertCircle className="h-4 w-4" />
                  {error}
                </div>
              )}

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Signing in..." : "Sign in and receive token"}
                {!loading && <ArrowRight className="ml-2 h-4 w-4" />}
              </Button>
            </form>

            <div className="mt-6 text-xs text-slate-500">
              JWT is stored in localStorage as <span className="text-slate-300">predictx_token</span> and automatically attached to API requests.
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
