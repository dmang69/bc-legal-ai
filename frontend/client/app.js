/* Client portal UI scaffold — no backend; accessibility-first demos */

const i18n = {
  en: {
    disclaimer:
      "Scaffold only. Do not upload confidential files to a public demo. Not legal advice.",
    preview: "Preview ready. Confirm classification and date, then connect API to process.",
  },
  "zh-Hans": {
    disclaimer: "演示骨架。请勿向公共演示上传保密文件。这不是法律意见。",
    preview: "预览就绪。确认分类与日期后，再连接 API 处理。",
  },
  pa: {
    disclaimer: "ਸਿਰਫ਼ ਡੈਮੋ ਢਾਂਚਾ। ਗੁਪਤ ਫਾਈਲਾਂ ਅਪਲੋਡ ਨਾ ਕਰੋ। ਇਹ ਕਾਨੂੰਨੀ ਸਲਾਹ ਨਹੀਂ।",
    preview: "ਪ੍ਰੀਵਿਊ ਤਿਆਰ। ਵਰਗੀਕਰਨ ਤੇ ਤਾਰੀਖ ਪੁਸ਼ਟੀ ਕਰੋ।",
  },
  tl: {
    disclaimer:
      "Scaffold lamang. Huwag mag-upload ng kumpidensyal na file sa public demo. Hindi legal advice.",
    preview: "Handa na ang preview. Kumpirmahin ang classification at petsa.",
  },
};

function setLang(code) {
  const t = i18n[code] || i18n.en;
  const d = document.getElementById("disclaimer");
  if (d) d.innerHTML = `<strong>${code}</strong> — ${t.disclaimer}`;
  document.documentElement.lang = code === "zh-Hans" ? "zh-Hans" : code;
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

setLang("en");
