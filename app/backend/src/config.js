const productionRequired = ["DATABASE_URL", "SERVICE_DATABASE_URL"];

if (process.env.NODE_ENV === "production") {
  for (const name of productionRequired) {
    if (!process.env[name]) {
      throw new Error(`Missing required environment variable: ${name}`);
    }
  }
  if (process.env.DIRECT_URL) {
    throw new Error(
      "DIRECT_URL must not be present in a long-lived service environment (owner credentials are migrate/CLI-only)",
    );
  }
}

export const config = Object.freeze({
  nodeEnv: process.env.NODE_ENV ?? "development",
  port: Number.parseInt(process.env.PORT ?? "4000", 10),
  databaseUrl: process.env.DATABASE_URL,
  serviceDatabaseUrl: process.env.SERVICE_DATABASE_URL,
});
