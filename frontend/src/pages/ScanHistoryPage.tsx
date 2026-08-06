import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Play, Square } from "lucide-react";

import { cancelScan, getScanHistory, startFullScan } from "../api/scans";
import { StatusBadge } from "../components/StatusBadge";
import { Button } from "../components/ui/Button";
import { useI18n } from "../i18n/I18nProvider";
import { formatDate } from "../utils/format";

export function ScanHistoryPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const historyQuery = useQuery({
    queryKey: ["scan-history"],
    queryFn: ({ signal }) => getScanHistory(signal),
    refetchInterval: 5000,
  });
  const startMutation = useMutation({
    mutationFn: () => startFullScan(false),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["scan-history"] }),
  });
  const cancelMutation = useMutation({
    mutationFn: cancelScan,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["scan-history"] }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{t("history.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("history.subtitle")}</p>
      </div>
      <div className="flex gap-2">
        <Button onClick={() => startMutation.mutate()}>
          <Play aria-hidden="true" size={16} />
          {t("actions.startScan")}
        </Button>
      </div>
      <div className="overflow-x-auto rounded-lg border border-border bg-background">
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead className="bg-muted text-muted-foreground">
            <tr>
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">{t("history.scanType")}</th>
              <th className="px-3 py-2">{t("history.status")}</th>
              <th className="px-3 py-2">{t("history.progress")}</th>
              <th className="px-3 py-2">{t("history.cacheHits")}</th>
              <th className="px-3 py-2">{t("history.errors")}</th>
              <th className="px-3 py-2">{t("history.started")}</th>
              <th className="px-3 py-2">{t("missing.actions")}</th>
            </tr>
          </thead>
          <tbody>
            {historyQuery.data?.map((scan) => (
              <tr key={scan.id} className="border-t border-border">
                <td className="px-3 py-2">{scan.id}</td>
                <td className="px-3 py-2">{scan.scan_type}</td>
                <td className="px-3 py-2">
                  <StatusBadge status={scan.status} />
                </td>
                <td className="px-3 py-2">
                  {scan.completed_item_count}/{scan.requested_item_count}
                </td>
                <td className="px-3 py-2">{scan.cache_hit_count}</td>
                <td className="px-3 py-2">{scan.error_count}</td>
                <td className="px-3 py-2">{formatDate(scan.started_at ?? scan.created_at)}</td>
                <td className="px-3 py-2">
                  {["queued", "running", "cancelling"].includes(scan.status) ? (
                    <Button variant="secondary" onClick={() => cancelMutation.mutate(scan.id)}>
                      <Square aria-hidden="true" size={14} />
                      {t("actions.cancel")}
                    </Button>
                  ) : null}
                </td>
              </tr>
            ))}
            {historyQuery.data?.length === 0 ? (
              <tr>
                <td className="px-3 py-6 text-muted-foreground" colSpan={8}>
                  {t("common.empty")}
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
