# Tenancy dispute intake

```
INTAKE: Tenancy Dispute
├─ Property / unit / rent / lease names
├─ Notice → service → dispute / deadline
├─ Prior RTB proceedings
├─ Current issues + evidence + landlord notice
└─ Personal circumstances (sensitive — consent required)
```

```python
answers = {
    "property_address": "123 Main St",
    "unit_designation": "990A",
    "tenancy_start_date": "2016-03-01",
    "current_rent": "1200",
    "lease_names": ["Tenant A", "Natalie"],
    "notice_received": True,
    "notice_date_received": "2025-11-12",
    "notice_method": "personal",
    "notice_type": "two_month",
    "dispute_filed": False,
    "issue_categories": ["habitability", "repairs"],
    "landlord_notified": True,
    "landlord_notified_how": "email",
    "landlord_notified_when": "2025-10-28",
}
intake = session.intake_from_answers(answers)
print(intake.format_tree())
print(intake.notice.dispute_deadline)  # rule-of-thumb; re-verify
```

Dispute windows (calendar days from received — **re-verify on RTB/RTA**):

| Notice | Days |
|--------|------|
| Ten day | 5 |
| One month | 10 |
| Two / four month | 15 |

Mailed service: engine **warns** that deemed receipt may add days — does not auto-add.
