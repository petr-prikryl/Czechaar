import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { flexRender, getCoreRowModel, useReactTable, type ColumnDef } from "@tanstack/react-table";
import {
  ChevronDown,
  ChevronRight,
  Copy,
  Download,
  ExternalLink,
  Info,
  RotateCw,
  Search,
  ShieldOff,
  Wrench,
} from "lucide-react";
import { Fragment, useMemo, useState } from "react";

import { ignoreMediaFile } from "../api/ignored";
import {
  createFfmpegRepairPlan,
  getAudioStreams,
  getMissingAudio,
  type FfmpegRepairPlan,
  type MediaFileSummary,
  type MediaItem,
} from "../api/media";
import { startMediaFileScan } from "../api/scans";
import { StatusBadge } from "../components/StatusBadge";
import { Button } from "../components/ui/Button";
import { useI18n } from "../i18n/I18nProvider";
import { formatDate, formatEpisodeCode } from "../utils/format";

export function MissingAudioPage() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [includeIgnored, setIncludeIgnored] = useState(false);
  const [page, setPage] = useState(1);
  const [expandedFileId, setExpandedFileId] = useState<number | null>(null);
  const params = new URLSearchParams({
    page: String(page),
    page_size: "50",
    include_ignored: String(includeIgnored),
  });
  if (search) {
    params.set("search", search);
  }

  const query = useQuery({
    queryKey: ["missing", search, includeIgnored, page],
    queryFn: ({ signal }) => getMissingAudio(params, signal),
  });
  const rescanMutation = useMutation({
    mutationFn: (mediaFileId: number) => startMediaFileScan(mediaFileId, true),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["missing"] }),
  });
  const ignoreMutation = useMutation({
    mutationFn: ignoreMediaFile,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["missing"] }),
  });

  const columns = useMemo<ColumnDef<MediaItem>[]>(
    () => [
      {
        id: "details",
        header: t("missing.reason"),
        cell: ({ row }) => {
          const fileId = row.original.media_file?.id;
          const isExpanded = fileId !== undefined && expandedFileId === fileId;
          return fileId ? (
            <Button
              aria-label={isExpanded ? t("missing.hideDetails") : t("missing.reason")}
              className="h-8 px-2"
              title={isExpanded ? t("missing.hideDetails") : t("missing.showDetails")}
              variant="secondary"
              onClick={() => setExpandedFileId(isExpanded ? null : fileId)}
            >
              {isExpanded ? (
                <ChevronDown aria-hidden="true" size={15} />
              ) : (
                <Info aria-hidden="true" size={15} />
              )}
              {isExpanded ? t("missing.hideDetails") : t("missing.reason")}
            </Button>
          ) : null;
        },
      },
      {
        header: t("missing.actions"),
        cell: ({ row }) => {
          const fileId = row.original.media_file?.id;
          return fileId ? (
            <div className="flex max-w-[300px] flex-wrap gap-2">
              {row.original.source_web_url ? (
                <a
                  className="inline-flex h-8 items-center justify-center gap-2 whitespace-nowrap rounded-md border border-border bg-background px-2 text-sm font-medium transition hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  href={row.original.source_web_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  <ExternalLink aria-hidden="true" size={14} />
                  {row.original.source_type === "radarr"
                    ? t("actions.openRadarr")
                    : t("actions.openSonarr")}
                </a>
              ) : null}
              <Button
                className="h-8 px-2"
                variant="secondary"
                onClick={() => rescanMutation.mutate(fileId)}
              >
                <RotateCw aria-hidden="true" size={14} />
                {t("actions.rescan")}
              </Button>
              <Button
                className="h-8 px-2"
                variant="ghost"
                onClick={() => ignoreMutation.mutate(fileId)}
              >
                <ShieldOff aria-hidden="true" size={14} />
                {t("actions.ignore")}
              </Button>
            </div>
          ) : null;
        },
      },
      { header: t("missing.type"), cell: ({ row }) => row.original.media_type },
      {
        header: t("missing.titleColumn"),
        cell: ({ row }) => row.original.series_title || row.original.title,
      },
      {
        header: t("missing.episode"),
        cell: ({ row }) =>
          formatEpisodeCode(row.original.season_number, row.original.episode_number),
      },
      { header: t("missing.quality"), cell: ({ row }) => row.original.media_file?.quality ?? "" },
      {
        header: t("missing.status"),
        cell: ({ row }) => <StatusBadge status={row.original.media_file?.scan_state} />,
      },
      {
        header: t("missing.lastScan"),
        cell: ({ row }) => formatDate(row.original.media_file?.last_scan_attempt),
      },
      {
        header: t("missing.path"),
        cell: ({ row }) => (
          <span className="block max-w-[360px] truncate">
            {row.original.media_file?.mapped_local_path}
          </span>
        ),
      },
    ],
    [expandedFileId, ignoreMutation, rescanMutation, t],
  );
  const table = useReactTable({
    data: query.data?.items ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
  });
  const exportHref = `/api/v1/missing/export.csv?${params.toString()}`;
  const totalPages = Math.max(
    1,
    Math.ceil((query.data?.total ?? 0) / (query.data?.page_size ?? 50)),
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">{t("missing.title")}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t("missing.subtitle")}</p>
        </div>
        <a
          className="inline-flex h-9 items-center gap-2 rounded-md border border-border px-3 text-sm"
          href={exportHref}
        >
          <Download aria-hidden="true" size={16} />
          {t("actions.exportCsv")}
        </a>
      </div>
      <div className="flex flex-col gap-3 rounded-lg border border-border bg-background p-3 md:flex-row md:items-center">
        <label className="flex min-w-0 flex-1 items-center gap-2">
          <Search aria-hidden="true" className="text-muted-foreground" size={16} />
          <input
            className="h-9 min-w-0 flex-1 bg-transparent text-sm outline-none"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            placeholder={t("filters.search")}
          />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={includeIgnored}
            onChange={(event) => {
              setIncludeIgnored(event.target.checked);
              setPage(1);
            }}
          />
          {t("filters.showIgnored")}
        </label>
      </div>
      <div className="overflow-x-auto rounded-lg border border-border bg-background">
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead className="bg-muted text-muted-foreground">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="px-3 py-2 font-medium">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {query.isLoading ? (
              <tr>
                <td className="px-3 py-6 text-muted-foreground" colSpan={columns.length}>
                  {t("common.loading")}
                </td>
              </tr>
            ) : table.getRowModel().rows.length === 0 ? (
              <tr>
                <td className="px-3 py-6 text-muted-foreground" colSpan={columns.length}>
                  {t("common.empty")}
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => {
                const fileId = row.original.media_file?.id;
                const isExpanded = fileId !== undefined && expandedFileId === fileId;
                return (
                  <Fragment key={row.id}>
                    <tr className="border-t border-border">
                      {row.getVisibleCells().map((cell) => (
                        <td key={cell.id} className="px-3 py-2 align-middle">
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </td>
                      ))}
                    </tr>
                    {isExpanded ? (
                      <tr className="border-t border-border bg-muted/40">
                        <td className="px-3 py-4" colSpan={columns.length}>
                          <MissingAudioDetails
                            file={row.original.media_file}
                            sourceType={row.original.source_type}
                          />
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
        <span>
          {t("common.page")} {page} {t("common.of")} {totalPages}
        </span>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            disabled={page <= 1}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
          >
            <ChevronRight aria-hidden="true" className="rotate-180" size={14} />
            {t("common.previous")}
          </Button>
          <Button
            variant="secondary"
            disabled={page >= totalPages}
            onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
          >
            {t("common.next")}
            <ChevronRight aria-hidden="true" size={14} />
          </Button>
        </div>
      </div>
    </div>
  );
}

function MissingAudioDetails({
  file,
  sourceType,
}: {
  file: MediaFileSummary | null;
  sourceType: MediaItem["source_type"];
}) {
  const { t } = useI18n();
  const [repairPlan, setRepairPlan] = useState<FfmpegRepairPlan | null>(null);
  const repairMutation = useMutation({
    mutationFn: (audioStreamId: number) => {
      if (!file) {
        throw new Error("Media file is not available.");
      }
      return createFfmpegRepairPlan(file.id, audioStreamId);
    },
    onSuccess: setRepairPlan,
  });
  const streamsQuery = useQuery({
    queryKey: ["audio-streams", file?.id],
    queryFn: ({ signal }) => getAudioStreams(file!.id, signal),
    enabled: file !== null,
  });

  if (!file) {
    return <p className="text-sm text-muted-foreground">{t("common.empty")}</p>;
  }

  const reason =
    file.error_code !== null
      ? `${t("missing.errorReason")}: ${file.error_code}`
      : t("missing.noCzechStreamMatch");
  const activeRepairPlan = repairPlan?.media_file_id === file.id ? repairPlan : null;

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(360px,1.3fr)]">
      <div className="space-y-3 text-sm">
        <div className="flex items-start gap-2">
          <Info aria-hidden="true" className="mt-0.5 text-muted-foreground" size={16} />
          <div>
            <p className="font-medium">{t("missing.details")}</p>
            <p className="text-muted-foreground">{reason}</p>
            {file.sanitized_error_message ? (
              <p className="mt-1 text-rose-700 dark:text-rose-300">
                {file.sanitized_error_message}
              </p>
            ) : null}
          </div>
        </div>
        <dl className="grid gap-2">
          <div>
            <dt className="text-muted-foreground">{t("missing.originalPath")}</dt>
            <dd className="break-all font-mono text-xs">{file.original_source_path}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("missing.mappedPath")}</dt>
            <dd className="break-all font-mono text-xs">
              {file.mapped_local_path ?? t("settings.noMappingMatched")}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">{t("missing.integration")}</dt>
            <dd>{sourceType === "radarr" ? "Radarr" : "Sonarr"}</dd>
          </div>
        </dl>
      </div>
      <div className="space-y-3">
        <div className="overflow-x-auto rounded-md border border-border bg-background">
          <table className="w-full min-w-[660px] text-left text-xs">
            <thead className="bg-muted text-muted-foreground">
              <tr>
                <th className="px-2 py-2">#</th>
                <th className="px-2 py-2">{t("missing.streamLanguage")}</th>
                <th className="px-2 py-2">{t("missing.streamTitle")}</th>
                <th className="px-2 py-2">{t("missing.codec")}</th>
                <th className="px-2 py-2">{t("missing.channels")}</th>
                <th className="px-2 py-2">{t("missing.matchReason")}</th>
                <th className="px-2 py-2">{t("missing.actions")}</th>
              </tr>
            </thead>
            <tbody>
              {streamsQuery.isLoading ? (
                <tr>
                  <td className="px-2 py-4 text-muted-foreground" colSpan={7}>
                    {t("common.loading")}
                  </td>
                </tr>
              ) : streamsQuery.data?.length === 0 ? (
                <tr>
                  <td className="px-2 py-4 text-muted-foreground" colSpan={7}>
                    {t("missing.noAudioStreams")}
                  </td>
                </tr>
              ) : (
                streamsQuery.data?.map((stream) => (
                  <tr key={stream.id} className="border-t border-border">
                    <td className="px-2 py-2">{stream.stream_index}</td>
                    <td className="px-2 py-2">
                      {stream.original_language || stream.normalized_language || "-"}
                    </td>
                    <td className="max-w-[220px] truncate px-2 py-2">
                      {stream.original_title || "-"}
                    </td>
                    <td className="px-2 py-2">{stream.codec_name || "-"}</td>
                    <td className="px-2 py-2">{stream.channels ?? "-"}</td>
                    <td className="px-2 py-2">{stream.match_reason}</td>
                    <td className="px-2 py-2">
                      <Button
                        className="h-8 px-2"
                        variant="secondary"
                        onClick={() => repairMutation.mutate(stream.id)}
                      >
                        <Wrench aria-hidden="true" size={14} />
                        {t("actions.repairMetadata")}
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {repairMutation.isError ? (
          <p className="text-sm text-rose-700 dark:text-rose-300">
            {t("common.error")}: {repairMutation.error.message}
          </p>
        ) : null}
        {activeRepairPlan ? (
          <div className="space-y-3 rounded-md border border-border bg-muted/40 p-3 text-sm">
            <div>
              <p className="font-medium">{t("missing.ffmpegRepair")}</p>
              <p className="mt-1 text-muted-foreground">{t("missing.ffmpegRepairHelp")}</p>
            </div>
            <div>
              <p className="text-muted-foreground">{t("missing.repairOutput")}</p>
              <p className="break-all font-mono text-xs">{activeRepairPlan.output_path}</p>
            </div>
            <pre className="max-h-44 overflow-auto rounded-md bg-background p-3 text-xs">
              {activeRepairPlan.display_command}
            </pre>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <Button
                className="w-full sm:w-auto"
                variant="secondary"
                onClick={() => {
                  void navigator.clipboard?.writeText(activeRepairPlan.display_command);
                }}
              >
                <Copy aria-hidden="true" size={14} />
                {t("actions.copyCommand")}
              </Button>
              <p className="text-xs text-muted-foreground">{t("missing.ffmpegRepairWarning")}</p>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
