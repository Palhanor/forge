import express from "express";

const app = express();
const port = Number(process.env.PORT) || 3000;

app.get("/ping", (_req, res) => {
  res.json({
    message: process.env.PING_MESSAGE ?? "pong",
    runtime: "typescript",
  });
});

app.listen(port, "0.0.0.0", () => {
  console.log(`nodejs-ping-ts listening on port ${port}`);
});
