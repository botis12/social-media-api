import DashboardLayout from "@/components/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

type QueueStats = {
  active: number;
  completed: number;
  failed: number;
  delayed: number;
  waiting: number;
};

const STAT_LABELS: { key: keyof QueueStats; label: string }[] = [
  { key: "active", label: "Active jobs" },
  { key: "waiting", label: "Waiting" },
  { key: "delayed", label: "Delayed" },
  { key: "completed", label: "Completed" },
  { key: "failed", label: "Failed" },
];

export default function Dashboard() {
  const [stats, setStats] = useState<QueueStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const res = await fetch("/api/stats");
        if (!res.ok) throw new Error(`Request failed (${res.status})`);
        const data = await res.json();
        if (!cancelled) {
          setStats(data.queue);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError((e as Error).message);
      }
    };

    load();
    const interval = setInterval(load, 10000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <DashboardLayout>
      <div className="flex flex-col gap-6">
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>

        {error ? (
          <p className="text-sm text-destructive">
            Could not load queue stats: {error}
          </p>
        ) : !stats ? (
          <Loader2 className="animate-spin" />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {STAT_LABELS.map(({ key, label }) => (
              <Card key={key}>
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {label}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-semibold">{stats[key] ?? 0}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
