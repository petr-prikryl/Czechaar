import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FolderCheck, Route, Save, TestTube2, Trash2 } from "lucide-react";
import { type FormEvent, useMemo, useState } from "react";

import { listIntegrations, type SourceType } from "../../api/integrations";
import {
  createMediaRoot,
  createPathMapping,
  deleteMediaRoot,
  deletePathMapping,
  listMediaRoots,
  listPathMappings,
  testPathMapping,
  type PathMappingCreate,
  type PathMappingTestResponse,
} from "../../api/pathSafety";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { useI18n } from "../../i18n/I18nProvider";

const mappingDefaults: PathMappingCreate = {
  integration_id: null,
  source_type: null,
  remote_path_prefix: "",
  local_path_prefix: "",
  enabled: true,
  priority: 100,
  description: "",
};

export function PathSafetySettings() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [mappingForm, setMappingForm] = useState<PathMappingCreate>(mappingDefaults);
  const [rootPath, setRootPath] = useState("");
  const [testPath, setTestPath] = useState("");
  const [testSourceType, setTestSourceType] = useState<SourceType>("radarr");
  const [testIntegrationId, setTestIntegrationId] = useState<number>(1);
  const [testResult, setTestResult] = useState<PathMappingTestResponse | null>(null);

  const mappingsQuery = useQuery({
    queryKey: ["path-mappings"],
    queryFn: ({ signal }) => listPathMappings(signal),
  });
  const rootsQuery = useQuery({
    queryKey: ["media-roots"],
    queryFn: ({ signal }) => listMediaRoots(signal),
  });
  const integrationsQuery = useQuery({
    queryKey: ["integrations"],
    queryFn: ({ signal }) => listIntegrations(signal),
  });

  const firstIntegrationId = useMemo(
    () => integrationsQuery.data?.[0]?.id ?? 1,
    [integrationsQuery.data],
  );

  const createMappingMutation = useMutation({
    mutationFn: createPathMapping,
    onSuccess: () => {
      setMappingForm(mappingDefaults);
      void queryClient.invalidateQueries({ queryKey: ["path-mappings"] });
    },
  });
  const deleteMappingMutation = useMutation({
    mutationFn: deletePathMapping,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["path-mappings"] }),
  });
  const createRootMutation = useMutation({
    mutationFn: createMediaRoot,
    onSuccess: () => {
      setRootPath("");
      void queryClient.invalidateQueries({ queryKey: ["media-roots"] });
    },
  });
  const deleteRootMutation = useMutation({
    mutationFn: deleteMediaRoot,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["media-roots"] }),
  });
  const testMappingMutation = useMutation({
    mutationFn: testPathMapping,
    onSuccess: setTestResult,
  });

  const submitMapping = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    createMappingMutation.mutate({
      ...mappingForm,
      remote_path_prefix: mappingForm.remote_path_prefix.trim(),
      local_path_prefix: mappingForm.local_path_prefix.trim(),
      description: mappingForm.description?.trim() || null,
    });
  };

  const submitRoot = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    createRootMutation.mutate({
      path: rootPath.trim(),
      enabled: true,
      description: null,
    });
  };

  const runMappingTest = () => {
    testMappingMutation.mutate({
      remote_path: testPath.trim(),
      source_type: testSourceType,
      integration_id: testIntegrationId || firstIntegrationId,
    });
  };

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Card className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">{t("settings.pathMappings")}</h2>
          <Route aria-hidden="true" className="text-muted-foreground" size={20} />
        </div>

        <div className="space-y-3">
          {mappingsQuery.data?.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t("settings.noPathMappings")}</p>
          ) : null}
          {mappingsQuery.data?.map((mapping) => (
            <div
              className="flex flex-col gap-3 rounded-md border border-border p-3"
              key={mapping.id}
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{mapping.source_type ?? t("settings.allSources")}</Badge>
                <Badge tone={mapping.enabled ? "success" : "warning"}>
                  {mapping.enabled ? t("common.enabled") : t("common.disabled")}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {t("settings.priority")} {mapping.priority}
                </span>
              </div>
              <p className="break-all text-sm">
                {mapping.remote_path_prefix}
                {" -> "}
                {mapping.local_path_prefix}
              </p>
              <Button
                className="w-fit"
                variant="secondary"
                onClick={() => deleteMappingMutation.mutate(mapping.id)}
                disabled={deleteMappingMutation.isPending}
              >
                <Trash2 aria-hidden="true" size={16} />
                {t("actions.delete")}
              </Button>
            </div>
          ))}
        </div>

        <form className="grid gap-3" onSubmit={submitMapping}>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block space-y-1 text-sm">
              <span className="font-medium">{t("settings.sourceType")}</span>
              <select
                className="h-10 w-full rounded-md border border-border bg-background px-3"
                value={mappingForm.source_type ?? "all"}
                onChange={(event) =>
                  setMappingForm((current) => ({
                    ...current,
                    source_type:
                      event.target.value === "all" ? null : (event.target.value as SourceType),
                  }))
                }
              >
                <option value="all">{t("settings.allSources")}</option>
                <option value="radarr">Radarr</option>
                <option value="sonarr">Sonarr</option>
              </select>
            </label>
            <label className="block space-y-1 text-sm">
              <span className="font-medium">{t("settings.priority")}</span>
              <input
                className="h-10 w-full rounded-md border border-border bg-background px-3"
                type="number"
                value={mappingForm.priority}
                onChange={(event) =>
                  setMappingForm((current) => ({
                    ...current,
                    priority: Number(event.target.value),
                  }))
                }
              />
            </label>
          </div>
          <label className="block space-y-1 text-sm">
            <span className="font-medium">{t("settings.remotePrefix")}</span>
            <input
              className="h-10 w-full rounded-md border border-border bg-background px-3"
              value={mappingForm.remote_path_prefix}
              onChange={(event) =>
                setMappingForm((current) => ({
                  ...current,
                  remote_path_prefix: event.target.value,
                }))
              }
              placeholder="/data/movies"
              required
            />
          </label>
          <label className="block space-y-1 text-sm">
            <span className="font-medium">{t("settings.localPrefix")}</span>
            <input
              className="h-10 w-full rounded-md border border-border bg-background px-3"
              value={mappingForm.local_path_prefix}
              onChange={(event) =>
                setMappingForm((current) => ({
                  ...current,
                  local_path_prefix: event.target.value,
                }))
              }
              placeholder="/movies"
              required
            />
          </label>
          <Button className="w-fit" type="submit" disabled={createMappingMutation.isPending}>
            <Save aria-hidden="true" size={16} />
            {t("settings.savePathMapping")}
          </Button>
        </form>

        <div className="space-y-3 border-t border-border pt-4">
          <h3 className="text-sm font-semibold">{t("settings.testPathMapping")}</h3>
          <div className="grid gap-3 sm:grid-cols-[1fr_140px_120px]">
            <input
              className="h-10 rounded-md border border-border bg-background px-3 text-sm"
              value={testPath}
              onChange={(event) => setTestPath(event.target.value)}
              placeholder="/data/movies/Avatar/movie.mkv"
            />
            <select
              className="h-10 rounded-md border border-border bg-background px-3 text-sm"
              value={testSourceType}
              onChange={(event) => setTestSourceType(event.target.value as SourceType)}
            >
              <option value="radarr">Radarr</option>
              <option value="sonarr">Sonarr</option>
            </select>
            <input
              className="h-10 rounded-md border border-border bg-background px-3 text-sm"
              min={1}
              type="number"
              value={testIntegrationId}
              onChange={(event) => setTestIntegrationId(Number(event.target.value))}
              aria-label={t("settings.integrationId")}
            />
          </div>
          <Button
            variant="secondary"
            onClick={runMappingTest}
            disabled={testMappingMutation.isPending || testPath.trim().length === 0}
          >
            <TestTube2 aria-hidden="true" size={16} />
            {t("settings.testPathMapping")}
          </Button>
          {testResult ? (
            <div className="rounded-md border border-border bg-muted p-3 text-sm">
              <Badge tone={testResult.mapped_path ? "success" : "warning"}>
                {testResult.status}
              </Badge>
              <p className="mt-2 break-all text-muted-foreground">
                {testResult.mapped_path ?? t("settings.noMappingMatched")}
              </p>
            </div>
          ) : null}
        </div>
      </Card>

      <Card className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">{t("settings.mediaRoots")}</h2>
          <FolderCheck aria-hidden="true" className="text-muted-foreground" size={20} />
        </div>

        <div className="space-y-3">
          {rootsQuery.data?.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t("settings.noMediaRoots")}</p>
          ) : null}
          {rootsQuery.data?.map((root) => (
            <div
              className="flex flex-col gap-3 rounded-md border border-border p-3 sm:flex-row sm:items-center sm:justify-between"
              key={root.id}
            >
              <div className="min-w-0">
                <p className="break-all text-sm font-medium">{root.path}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <Badge tone={root.exists ? "success" : "danger"}>
                    {root.exists ? t("settings.exists") : t("settings.missing")}
                  </Badge>
                  <Badge tone={root.readable ? "success" : "warning"}>
                    {root.readable ? t("settings.readable") : t("settings.notReadable")}
                  </Badge>
                </div>
              </div>
              <Button
                variant="secondary"
                onClick={() => deleteRootMutation.mutate(root.id)}
                disabled={deleteRootMutation.isPending}
              >
                <Trash2 aria-hidden="true" size={16} />
                {t("actions.delete")}
              </Button>
            </div>
          ))}
        </div>

        <form className="flex flex-col gap-3 sm:flex-row" onSubmit={submitRoot}>
          <label className="min-w-0 flex-1 space-y-1 text-sm">
            <span className="font-medium">{t("settings.mediaRootPath")}</span>
            <input
              className="h-10 w-full rounded-md border border-border bg-background px-3"
              value={rootPath}
              onChange={(event) => setRootPath(event.target.value)}
              placeholder="/movies"
              required
            />
          </label>
          <Button
            className="self-end"
            type="submit"
            disabled={createRootMutation.isPending || rootPath.trim().length === 0}
          >
            <Save aria-hidden="true" size={16} />
            {t("settings.saveMediaRoot")}
          </Button>
        </form>
      </Card>
    </div>
  );
}
