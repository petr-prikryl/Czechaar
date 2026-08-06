export function formatEpisodeCode(season: number | null, episode: number | null) {
  if (season === null || episode === null) {
    return "";
  }
  return `S${season.toString().padStart(2, "0")}E${episode.toString().padStart(2, "0")}`;
}

export function formatDate(value: string | null | undefined) {
  if (!value) {
    return "";
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
