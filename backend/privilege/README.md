# Privilege layer

## Chat guard — third-party disclosure

```python
from backend.privilege import guard_user_message

result = session.check_privilege_message(
    "I was discussing my case with my neighbor."
)
if result["alert_text"]:
    print(result["alert_text"])
```

```
⚠ PRIVILEGE ALERT:
Your message mentions discussing case details with a third party
(your neighbor). Communications with non-parties may not be protected
by solicitor-client privilege. Consider whether this information
should be shared before proceeding.
```

Soft warn by default (`requires_ack`). Use `block_send=True` to hard-stop UI send.

Does **not** decide waiver or privilege — caution only; ask a lawyer.
