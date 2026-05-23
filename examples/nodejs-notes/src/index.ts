import express from "express";
import { PrismaClient } from "@prisma/client";

const app = express();
const port = Number(process.env.PORT) || 3000;
const prisma = new PrismaClient();

app.use(express.json());

app.get("/ping", (_req, res) => {
  res.json({ message: "pong", runtime: "nodejs-notes" });
});

app.post("/notes", async (req, res) => {
  const { key, value } = req.body ?? {};
  if (typeof key !== "string" || !key.trim() || typeof value !== "string") {
    res.status(400).json({ error: "body must include string 'key' and 'value'" });
    return;
  }

  const note = await prisma.note.upsert({
    where: { key: key.trim() },
    create: { key: key.trim(), value },
    update: { value },
  });
  res.status(201).json(note);
});

app.get("/notes/:key", async (req, res) => {
  const note = await prisma.note.findUnique({
    where: { key: req.params.key },
  });
  if (!note) {
    res.status(404).json({ error: "not found" });
    return;
  }
  res.json(note);
});

app.listen(port, "0.0.0.0", () => {
  console.log(`nodejs-notes listening on port ${port}`);
});
