//! BC Legal AI Associate — Tauri 2 shell library.
//! Connects the shared web UI to a private backend. Not a lawyer.

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .run(tauri::generate_context!())
        .expect("error while running BC Legal AI Associate");
}
