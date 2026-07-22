# Conversational Platform Implementation Status

## Completed in this scaffold

- Responsive three-panel conversational interface
- Synthetic matter selector
- Chat history and new-chat workflow
- Model/reasoning mode selector
- Specialist agent selector
- Mock streaming assistant service
- Citation/source cards
- Evidence, draft, timeline, and agent panels
- Public-demo sensitive-text blocking
- Public-demo upload blocking
- Tauri 2 Rust shell
- Windows NSIS/MSI configuration
- macOS app/DMG configuration
- Android/iOS mobile window configuration
- Development build workflows for Windows and macOS

## Next required implementation

1. Normalize the monorepo and generate `package-lock.json`.
2. Install Rust and Tauri prerequisites in a development environment.
3. Run the first Windows development build.
4. Connect the UI to a private FastAPI conversation endpoint.
5. Add real authentication and matter isolation.
6. Add persistent conversation storage.
7. Add secure upload quarantine and ingestion.
8. Add retrieval, citations, model routing, and agent orchestration.
9. Add Android and iOS generated projects.
10. Add signing and store-distribution credentials.

## Security restriction

This scaffold must remain synthetic until Priority Zero repository remediation and the secure backend foundation are complete.
