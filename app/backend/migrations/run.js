import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import pg from "pg";

const { Client } = pg;
const directUrl = process.env.DIRECT_URL;

if (!directUrl) {
  throw new Error("Missing required environment variable: DIRECT_URL");
}

const migrationDirectory = path.dirname(fileURLToPath(import.meta.url));
const client = new Client({ connectionString: directUrl });

await client.connect();

try {
  await client.query("SELECT pg_advisory_lock($1)", [7401]);
  await client.query(`
    CREATE TABLE IF NOT EXISTS schema_migrations (
      version text PRIMARY KEY,
      applied_at timestamptz NOT NULL DEFAULT now()
    )
  `);

  const files = (await readdir(migrationDirectory))
    .filter((file) => /^\d+.*\.sql$/.test(file))
    .sort();

  for (const file of files) {
    const existing = await client.query(
      "SELECT 1 FROM schema_migrations WHERE version = $1",
      [file],
    );
    if (existing.rowCount) continue;

    const sql = await readFile(path.join(migrationDirectory, file), "utf8");
    await client.query("BEGIN");
    try {
      await client.query(sql);
      await client.query(
        "INSERT INTO schema_migrations(version) VALUES ($1)",
        [file],
      );
      await client.query("COMMIT");
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    }
  }

  console.log(JSON.stringify({ event: "migrations_complete", count: files.length }));
} finally {
  await client.query("SELECT pg_advisory_unlock($1)", [7401]).catch(() => {});
  await client.end();
}
