import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { flexRender, getCoreRowModel, useReactTable, type ColumnDef } from "@tanstack/react-table";
import { Download, RotateCw, Search, ShieldOff } from "lucide-react";
import { useMemo, useState } from "react";

import { ignoreMediaFile } from "../api/ignored";
import { getMissingAudio, type MediaItem } from "../api/media";
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
  const params = new URLSearchParams({
    page: "1",
    page_size: "100",
    include_ignored: String(includeIgnored),
  });
  if (search) {
    params.set("search", search);
  }

  const query = useQuery({
    queryKey: ["missing", search, includeIgnored],
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
      {
        header: t("missing.actions"),
        cell: ({ row }) => {
          const fileId = row.original.media_file?.id;
          return fileId ? (
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => rescanMutation.mutate(fileId)}>
                <RotateCw aria-hidden="true" size={14} />
                {t("actions.rescan")}
              </Button>
              <Button variant="ghost" onClick={() => ignoreMutation.mutate(fileId)}>
                <ShieldOff aria-hidden="true" size={14} />
                {t("actions.ignore")}
              </Button>
            </div>
          ) : null;
        },
      },
    ],
    [ignoreMutation, rescanMutation, t],
  );
  const table = useReactTable({
    data: query.data?.items ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
  });
  const exportHref = `/api/v1/missing/export.csv?${params.toString()}`;

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
            onChange={(event) => setSearch(event.target.value)}
            placeholder={t("filters.search")}
          />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={includeIgnored}
            onChange={(event) => setIncludeIgnored(event.target.checked)}
          />
          {t("filters.showIgnored")}
        </label>
      </div>
      <div className="overflow-x-auto rounded-lg border border-border bg-background">
        <table className="w-full min-w-[980px] text-left text-sm">
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
              table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="border-t border-border">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-3 py-2 align-middle">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
