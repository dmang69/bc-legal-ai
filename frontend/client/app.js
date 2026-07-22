/* BC Legal AI Associate — client shell (PWA + desktop webview) */

const i18n = {
  en: {
    disclaimer:
      "Scaffold / local platform. Do not put confidential files on public demos. Not legal advice.",
    preview: "Preview ready. Confirm classification and date before processing.",
  },
  "zh-Hans": {
    disclaimer: "本地/脚手架平台。请勿向公共演示上传保密文件。这不是法律意见。",
    preview: "预览就绪。确认分类与日期后再处理。",
  },
  pa: {
    disclaimer: "ਸਥਾਨਕ ਪਲੇਟਫਾਰਮ। ਗੁਪਤ ਫਾਈਲਾਂ ਪਬਲਿਕ ਡੈਮੋ ਤੇ ਨਾ ਪਾਓ। ਇਹ ਕਾਨੂੰਨੀ ਸਲਾਹ ਨਹੀਂ।",
    preview: "ਪ੍ਰੀਵਿਊ ਤਿਆਰ। ਵਰਗੀਕਰਨ ਤੇ ਤਾਰੀਖ ਪੁਸ਼ਟੀ ਕਰੋ।",
  },
  tl: {
    disclaimer:
      "Local platform. Huwag maglagay ng kumpidensyal na file sa public demo. Hindi legal advice.",
    preview: "Handa na ang preview. Kumpirmahin ang classification at petsa.",
  },
};

function setLang(code) {
  const t = i18n[code] || i18n.en;
  const d = document.getElementById("disclaimer");
  if (d) d.innerHTML = `<strong>${code}</strong> — ${t.disclaimer}`;
  document.documentElement.lang = code === "zh-Hans" ? "zh-Hans" : code;
}

async function checkApi() {
  const el = document.getElementById("api-status");
  const dash = document.getElementById("dash-empty");
  try {
    const r = await fetch("/health", { cache: "no-store" });
    if (!r.ok) throw new Error(String(r.status));
    const j = await r.json();
    if (el) el.textContent = `API: ${j.status} · phase ${j.phase || "?"} · ${j.mode || ""}`;
    if (dash) {
      dash.textContent =
        "API connected. Use /docs for Phase 3–4 / 4-4 endpoints (consent, JR clock, post-resolution).";
    }
  } catch {
    if (el) el.textContent = "API: offline — start launcher or uvicorn backend.api.main:app";
  }
}

async function runJrClock() {
  const out = document.getElementById("jr-out");
  const date = document.getElementById("jr-date")?.value;
  if (!out) return;
  out.textContent = "Calculating…";
  try {
    const r = await fetch("/v1/deadlines/jr-clock", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        matter_id: "DEMO-UI",
        issuance_date: date,
        finality_known: true,
        human_confirmed: false,
      }),
    });
    const j = await r.json();
    out.textContent = JSON.stringify(j, null, 2);
  } catch (e) {
    out.textContent = "JR clock failed — is the API running?\n" + String(e);
  }
}

document.getElementById("lang")?.addEventListener("change", (e) => {
  setLang(e.target.value);
});

document.getElementById("preview-btn")?.addEventListener("click", () => {
  const code = document.getElementById("lang")?.value || "en";
  const t = i18n[code] || i18n.en;
  const status = document.getElementById("upload-status");
  const file = document.getElementById("file")?.files?.[0];
  const cls = document.getElementById("class")?.value;
  const dt = document.getElementById("meta-date")?.value;
  if (status) {
    status.textContent = file
      ? `${t.preview} (${file.name} · ${cls} · ${dt || "no date"})`
      : t.preview;
  }
});

document.getElementById("jr-btn")?.addEventListener("click", runJrClock);

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

setLang("en");
checkApi();
