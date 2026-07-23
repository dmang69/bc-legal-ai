# TODO: Refactor to Annotated Type Hints for FastAPI DI

## Step-by-Step Plan

- [x] Task analysis and exhaustive codebase review completed
- [ ] **Step 1:** Create `backend/api/dependencies.py` with `CurrentUser` Annotated type alias
- [ ] **Step 2:** Edit `backend/api/platform_routes.py`:
  - [ ] Remove `Header` from imports
  - [ ] Add import: `from backend.api.dependencies import CurrentUser`
  - [ ] Delete the `_user()` helper function
  - [ ] Refactor all 27 auth-protected routes to use `current_user: CurrentUser`
  - [ ] Fix `logout()` to properly validate auth (returns 401 on bad token)
  - [ ] Fix `audit_verify()` to not discard resolved user
  - [ ] Fix `evaluate_ai_consent()` to not discard resolved user
- [ ] **Step 3:** Validate: import-check `platform_routes` module
- [ ] **Step 4:** Optional: run pytest if tests exist

