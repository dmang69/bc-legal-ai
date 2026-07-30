/**
 * Verify Tauri install/upgrade configuration is consistent.
 * Does not require a full native build.
 */
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const tauriDir = join(root, "src-tauri");
const errors = [];
const ok = (m) => console.log(`  ✓ ${m}`);
const fail = (m) => {
  errors.push(m);
  console.error(`  ✗ ${m}`);
};

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

console.log("== BC Legal AI — upgrade/install config verification ==\n");

const conf = readJson(join(tauriDir, "tauri.conf.json"));
const win = readJson(join(tauriDir, "tauri.windows.conf.json"));
const cargo = readFileSync(join(tauriDir, "Cargo.toml"), "utf8");
const pkg = readJson(join(root, "package.json"));
const caps = readJson(join(tauriDir, "capabilities", "default.json"));
const libRs = readFileSync(join(tauriDir, "src", "lib.rs"), "utf8");

// Version alignment
const confVer = conf.version;
const cargoVer = (cargo.match(/^version\s*=\s*"([^"]+)"/m) || [])[1];
const pkgVer = pkg.version;
console.log("Versions:");
if (confVer && cargoVer && confVer === cargoVer) ok(`tauri.conf == Cargo.toml == ${confVer}`);
else fail(`version mismatch conf=${confVer} cargo=${cargoVer}`);
if (pkgVer === confVer) ok(`package.json == ${pkgVer}`);
else fail(`package.json version ${pkgVer} != ${confVer}`);

// Stable product identity (required for Windows upgrade)
console.log("\nProduct identity (must stay stable across upgrades):");
if (conf.identifier === "ca.bclegalai.associate") ok(`identifier=${conf.identifier}`);
else fail(`unexpected identifier: ${conf.identifier}`);
if (conf.productName === "BC Legal AI Associate") ok(`productName=${conf.productName}`);
else fail(`unexpected productName: ${conf.productName}`);

// Updater plugin (artifacts optional for local NSIS upgrade; enable for Release auto-update)
console.log("\nAuto-updater:");
if (conf.bundle?.createUpdaterArtifacts === true) {
  ok("createUpdaterArtifacts=true (release auto-update packages)");
} else if (conf.bundle?.createUpdaterArtifacts === false) {
  ok("createUpdaterArtifacts=false (local/CI installer build; set true + signing key for auto-update packages)");
} else {
  fail("bundle.createUpdaterArtifacts must be boolean");
}
const updater = conf.plugins?.updater;
if (updater?.pubkey && updater.pubkey.length > 40) ok("plugins.updater.pubkey set");
else fail("plugins.updater.pubkey missing");
if (Array.isArray(updater?.endpoints) && updater.endpoints.length) {
  ok(`endpoints: ${updater.endpoints.join(", ")}`);
  if (updater.endpoints.some((e) => e.includes("latest.json"))) ok("endpoint serves latest.json");
  else fail("endpoint should point at latest.json on Releases");
} else fail("plugins.updater.endpoints missing");
if (updater?.windows?.installMode) ok(`windows installMode=${updater.windows.installMode}`);
else fail("plugins.updater.windows.installMode missing");
if (process.env.ALA_REQUIRE_UPDATER_ARTIFACTS === "1" && conf.bundle?.createUpdaterArtifacts !== true) {
  fail("ALA_REQUIRE_UPDATER_ARTIFACTS=1 requires createUpdaterArtifacts=true");
}

// Windows NSIS / MSI upgrade surface
console.log("\nWindows installers:");
const nsis = win.bundle?.windows?.nsis;
const targets = win.bundle?.targets || [];
if (targets.includes("nsis")) ok("NSIS target enabled");
else fail("NSIS target missing");
if (targets.includes("msi")) ok("MSI target enabled");
else fail("MSI target missing");
if (nsis?.installMode === "currentUser" || nsis?.installMode === "perUser") {
  ok(`NSIS installMode=${nsis.installMode} (in-place upgrade friendly)`);
} else fail(`NSIS installMode should be currentUser/perUser, got ${nsis?.installMode}`);
const upgradeCode = win.bundle?.windows?.wix?.upgradeCode;
if (upgradeCode && /^[0-9A-Fa-f-]{36}$/.test(upgradeCode)) ok(`WiX upgradeCode stable: ${upgradeCode}`);
else fail("WiX upgradeCode must be a fixed GUID for MSI major upgrades");

// Rust plugins wired
console.log("\nNative shell:");
if (libRs.includes("tauri_plugin_updater")) ok("lib.rs registers updater plugin");
else fail("lib.rs missing tauri_plugin_updater");
if (libRs.includes("tauri_plugin_process")) ok("lib.rs registers process plugin (restart after update)");
else fail("lib.rs missing process plugin");
if (caps.permissions?.includes("updater:default")) ok("capabilities include updater:default");
else fail("capabilities missing updater:default");
if (caps.permissions?.includes("process:default")) ok("capabilities include process:default");
else fail("capabilities missing process:default");
if (cargo.includes("tauri-plugin-updater")) ok("Cargo.toml has tauri-plugin-updater");
else fail("Cargo.toml missing tauri-plugin-updater");

// PWA / web install surface
console.log("\nChrome PWA:");
const manifestPath = join(root, "..", "platform-ui", "public", "manifest.webmanifest");
const indexPath = join(root, "..", "platform-ui", "index.html");
if (existsSync(manifestPath)) {
  const man = readJson(manifestPath);
  if (man.display === "standalone") ok("manifest display=standalone");
  else fail("manifest display should be standalone");
  if (man.start_url) ok(`start_url=${man.start_url}`);
} else fail("platform-ui/public/manifest.webmanifest missing");
const indexHtml = readFileSync(indexPath, "utf8");
if (indexHtml.includes('rel="manifest"')) ok("index.html links manifest");
else fail("index.html missing manifest link");

// Mobile store upgrade note (config presence)
console.log("\nMobile store configs:");
for (const f of ["tauri.android.conf.json", "tauri.ios.conf.json", "tauri.macos.conf.json"]) {
  if (existsSync(join(tauriDir, f))) ok(f);
  else fail(`missing ${f}`);
}

console.log("\n== Result ==");
if (errors.length) {
  console.error(`FAILED (${errors.length} issue(s))`);
  process.exit(1);
}
console.log("PASS — install/upgrade configuration is consistent.");
console.log(`
Next (manual / CI):
  1. Build Windows v${confVer}: scripts\\\\build_windows_installer.ps1
  2. Install .exe, then build a higher version and reinstall → must upgrade in place
  3. Publish signed artifacts + latest.json to GitHub Releases for auto-update
  4. Mobile: Play/App Store versionCode/build number must increase each release
`);
