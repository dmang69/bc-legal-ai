# EvidenceNode Schema

```json
{
  "node_id": "EV-2026-000147",
  "doc_hash": "sha256:9f2a...",
  "privilege_class": "PROTECTED",
  "source_type": "PHOTO",
  "date_created": "2025-11-12T00:00:00-08:00",
  "date_received": "2025-11-17T14:22:00-08:00",
  "date_entered_system": "2026-07-21T14:41:16-05:00",
  "custodian": "tenant",
  "authenticity_status": "VERIFIED",
  "hearsay_flag": false,
  "best_evidence_rule": "ORIGINAL",
  "extracted_text": "On November 12, 2025...",
  "key_facts": [
    {
      "fact": "Eviction notice served on tenant",
      "confidence": 0.98,
      "source_span": "para_3_lines_11-14"
    }
  ],
  "entities_mentioned": [
    {
      "name": "Daniel Owings",
      "role": "landlord",
      "mention_count": 7
    }
  ],
  "corroborates": ["node_id", "node_id"],
  "contradicts": ["node_id"],
  "causally_linked_to": ["node_id"],
  "temporal_sequence": {
    "before": ["node_id"],
    "after": ["node_id"]
  },
  "chain_of_custody": [
    {
      "holder": "tenant",
      "from": "2025-11-12",
      "to": "present",
      "method": "physical_possession"
    }
  ],
  "alteration_history": [],
  "exhibit_number": null,
  "admissibility_assessment": {
    "likely_admissible": true,
    "grounds": ["relevant_s10_EA", "business_records_s22"],
    "risks": ["possible_hearsay_objection_on_paragraph_7"],
    "foundation_witness": "tenant"
  }
}
```

## Field Descriptions

- **node_id:** Unique immutable identifier (sequential)
- **doc_hash:** SHA256 of source file (tamper detection)
- **privilege_class:** Classification from Layer 0 tagger
- **source_type:** Document category (photo, email, decision, etc.)
- **dates:** Created, received, entered system
- **custodian:** Who produced/possesses the evidence
- **authenticity_status:** VERIFIED / DISPUTED / UNVERIFIED
- **best_evidence_rule:** ORIGINAL / CERTIFIED_COPY / PHOTOCOPY / DIGITAL
- **extracted_text:** OCR or manual transcript
- **key_facts:** Discrete factual claims extractable from the node
- **entities:** People, organizations, dates mentioned
- **relationships:** Corroboration, contradiction, causation, temporal links
- **chain_of_custody:** Provenance chain from creation to present
- **admissibility_assessment:** Evidence law analysis
