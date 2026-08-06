export type HealthResponse = {
  status: string;
};

export type ReadinessResponse = {
  status: string;
  database: boolean;
  migrationsApplied: boolean;
  initialized: boolean;
};
