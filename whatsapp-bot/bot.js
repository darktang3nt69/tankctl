const express = require("express");
const qrcode = require("qrcode-terminal");
const { Client, LocalAuth } = require("whatsapp-web.js");

const app = express();
app.use(express.json());

const SESSION_PATH = process.env.WHATSAPP_SESSION_PATH || "./session";
const PORT = Number(process.env.WHATSAPP_BOT_PORT || 3001);
const ALLOWED_NUMBERS = (process.env.WHATSAPP_ALLOWED_NUMBERS || "")
  .split(",")
  .map((n) => n.trim())
  .filter(Boolean);

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: SESSION_PATH }),
  puppeteer: {
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--single-process",
    ],
    executablePath: process.env.CHROME_EXECUTABLE_PATH || "/usr/bin/chromium",
  },
});

let ready = false;

client.on("qr", (qr) => {
  console.log("Scan this QR code with WhatsApp:");
  qrcode.generate(qr, { small: true });
});

client.on("ready", () => {
  ready = true;
  console.log("WhatsApp bot ready");
});

client.on("disconnected", (reason) => {
  ready = false;
  console.log(`WhatsApp disconnected: ${reason}`);
});

const disableClient = process.env.WHATSAPP_DISABLE_CLIENT === "true";
if (disableClient) {
  console.log("WhatsApp client disabled by WHATSAPP_DISABLE_CLIENT=true");
} else {
  client.initialize().catch((error) => {
    ready = false;
    console.error("WhatsApp client initialization failed:", error.message);
    console.error("Stack:", error.stack);
    process.exit(1);
  });
}

app.get("/health", (_req, res) => {
  res.json({ status: ready ? "ready" : "starting" });
});

app.get("/info", async (_req, res) => {
  try {
    if (!ready) {
      return res.status(503).json({ error: "WhatsApp client not ready" });
    }
    const info = await client.getMe();
    return res.json({
      phone: info.id._serialized,
      status: "authenticated",
      name: info.name || "WhatsApp User"
    });
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
});

app.post("/send", async (req, res) => {
  try {
    const { number, message } = req.body || {};

    if (!number || !message) {
      return res.status(400).json({ error: "number and message are required" });
    }

    if (ALLOWED_NUMBERS.length > 0 && !ALLOWED_NUMBERS.includes(number)) {
      return res.status(403).json({ error: "number not allowed" });
    }

    if (!ready) {
      return res.status(503).json({ error: "whatsapp client not ready" });
    }

    const chatId = `${number}@c.us`;
    await client.sendMessage(chatId, message);

    return res.json({ status: "sent" });
  } catch (error) {
    console.error("Send failed", error);
    return res.status(500).json({ error: "send failed" });
  }
});

app.listen(PORT, () => {
  console.log(`WhatsApp API running on port ${PORT}`);
});
