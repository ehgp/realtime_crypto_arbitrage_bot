import { randomUUID } from "node:crypto";

import cors from "cors";
import express from "express";
import helmet from "helmet";
import pino from "pino";

import { config } from "./config.js";

const logger = pino();
const app = express();

app.use(helmet());
app.use(cors());
app.use(express.json());
app.use((request, response, next) => {
  const requestId = request.get("x-request-id") ?? randomUUID();
  request.requestId = requestId;
  response.set("x-request-id", requestId);
  response.on("finish", () => {
    logger.info({
      request_id: requestId,
      method: request.method,
      path: request.path,
      status_code: response.statusCode,
    });
  });
  next();
});

app.get("/health", (_request, response) => {
  response.json({ ok: true });
});

app.use((_request, response) => {
  response.status(404).json({
    error: { code: "not_found", message: "Route not found" },
  });
});

app.listen(config.port, "0.0.0.0", () => {
  logger.info({ event: "backend_started", port: config.port });
});
