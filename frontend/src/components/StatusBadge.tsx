import { Badge } from "./ui/Badge";

export function StatusBadge({ status }: { status: string | null | undefined }) {
  const value = status ?? "unknown";
  const tone =
    value.includes("found") || value === "completed"
      ? "success"
      : value.includes("missing") || value.includes("queued") || value.includes("running")
        ? "warning"
        : value === "not_scanned"
          ? "neutral"
          : "danger";

  return <Badge tone={tone}>{value.replaceAll("_", " ")}</Badge>;
}
