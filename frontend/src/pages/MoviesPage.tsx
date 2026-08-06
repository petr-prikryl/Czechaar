import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RotateCw } from "lucide-react";

import { getMovies } from "../api/media";
import { startMediaFileScan } from "../api/scans";
import { StatusBadge } from "../components/StatusBadge";
import { Button } from "../components/ui/Button";
import { useI18n } from "../i18n/I18nProvider";
import { formatDate } from "../utils/format";

export function MoviesPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const moviesQuery = useQuery({
    queryKey: ["movies"],
    queryFn: ({ signal }) => getMovies(signal),
  });
  const rescanMutation = useMutation({
    mutationFn: (mediaFileId: number) => startMediaFileScan(mediaFileId, true),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["movies"] }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{t("movies.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("movies.subtitle")}</p>
      </div>
      <div className="overflow-x-auto rounded-lg border border-border bg-background">
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead className="bg-muted text-muted-foreground">
            <tr>
              <th className="px-3 py-2">{t("movies.titleColumn")}</th>
              <th className="px-3 py-2">{t("movies.year")}</th>
              <th className="px-3 py-2">{t("movies.quality")}</th>
              <th className="px-3 py-2">{t("movies.scanState")}</th>
              <th className="px-3 py-2">{t("movies.lastScan")}</th>
              <th className="px-3 py-2">{t("missing.actions")}</th>
            </tr>
          </thead>
          <tbody>
            {moviesQuery.isLoading ? (
              <tr>
                <td className="px-3 py-6 text-muted-foreground" colSpan={6}>
                  {t("common.loading")}
                </td>
              </tr>
            ) : null}
            {moviesQuery.data?.items.map((movie) => (
              <tr key={movie.id} className="border-t border-border">
                <td className="px-3 py-2 font-medium">{movie.title}</td>
                <td className="px-3 py-2">{movie.year}</td>
                <td className="px-3 py-2">{movie.media_file?.quality}</td>
                <td className="px-3 py-2">
                  <StatusBadge status={movie.media_file?.scan_state} />
                </td>
                <td className="px-3 py-2">{formatDate(movie.media_file?.last_scan_attempt)}</td>
                <td className="px-3 py-2">
                  {movie.media_file ? (
                    <Button
                      variant="secondary"
                      onClick={() => rescanMutation.mutate(movie.media_file!.id)}
                    >
                      <RotateCw aria-hidden="true" size={14} />
                      {t("actions.rescan")}
                    </Button>
                  ) : null}
                </td>
              </tr>
            ))}
            {moviesQuery.data?.items.length === 0 ? (
              <tr>
                <td className="px-3 py-6 text-muted-foreground" colSpan={6}>
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
