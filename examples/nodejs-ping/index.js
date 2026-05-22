const express = require("express");

const app = express();
const port = Number(process.env.PORT) || 3000;

app.get("/ping", (_req, res) => {
  res.json({ message: process.env.PING_MESSAGE ?? "pong" });
});

app.listen(port, "0.0.0.0", () => {
  console.log(`nodejs-ping listening on port ${port}`);
});
