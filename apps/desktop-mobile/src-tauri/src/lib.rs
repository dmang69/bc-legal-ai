#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Desktop: auto-updater checks GitHub Releases (see plugins.updater in tauri.conf.json).
    // Mobile store updates are delivered by Play / App Store — not this plugin.
    let mut builder = tauri::Builder::default();

    #[cfg(desktop)]
    {
        builder = builder
            .plugin(tauri_plugin_updater::Builder::new().build())
            .plugin(tauri_plugin_process::init());
    }

    builder
        .run(tauri::generate_context!())
        .expect("error while running BC Legal AI Associate");
}
