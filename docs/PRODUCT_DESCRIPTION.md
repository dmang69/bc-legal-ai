# BC Legal AI Associate

## Integrated Legal Practice and Litigation Support Platform

> **Document role:** Official product description for the **completed / target platform**.  
> **Interaction model:** Conversational AI legal workspace (not a traditional case-management shell only). See `docs/CONVERSATIONAL_WORKSPACE_SPEC.md`.  
> **Current maturity:** Prototype → Internal Alpha foundation (~30–35%). See `PRODUCT_STATUS.md` and `docs/PHASE_4_MASTER_ENGINEERING_PROGRAM.md` for what is implemented today.  
> **Public rule:** Do not market capabilities as live unless the corresponding milestone gate has passed.

BC Legal AI Associate is an advanced, human-supervised legal technology platform designed to improve the efficiency, organization, and accuracy of legal work in British Columbia.

The platform combines legal research, document drafting, matter management, scheduling, communications, evidence organization, and procedural support within a secure, matter-specific workspace. It is intended to reduce administrative burden, improve access to relevant information, and help legal professionals and authorized users manage complex legal records more effectively.

## Legal Document Drafting

The platform supports the preparation and refinement of a broad range of legal and administrative documents, including:

* contracts and agreements;
* petitions and responses;
* notices of application and application responses;
* affidavits and exhibit schedules;
* written submissions and legal memoranda;
* correspondence and demand letters;
* Residential Tenancy Branch materials;
* judicial-review documents;
* Books of Authorities;
* Books of Documents;
* chronologies, evidence indexes, and hearing outlines;
* standard legal and court forms.

Drafts are generated from verified matter information, approved evidence, applicable legal tests, and validated authorities. Unsupported facts, unresolved assumptions, unverified citations, and procedural uncertainties are flagged for human review.

No document is treated as ready for filing, service, signature, or external delivery until the applicable evidence, citation, privilege, procedural, and human-approval checks have been completed.

## Calendar, Deadline, and Task Management

The platform includes a rules-based matter calendar capable of organizing:

* court and tribunal dates;
* filing and service deadlines;
* limitation periods;
* client appointments;
* hearings;
* internal review dates;
* evidence-production dates;
* compliance deadlines;
* enforcement steps;
* judicial-review time limits;
* lawyer and staff tasks.

Deadline calculations are based on the governing forum, document type, service method, deemed-service rules, holidays, extension authority, and matter-specific facts.

Potential or uncertain dates are clearly distinguished from deadlines that have been confirmed by a qualified human reviewer.

## Secure Communications

The communications module supports authorized correspondence among lawyers, clients, staff, experts, witnesses, and other permitted participants.

Functions may include:

* drafting emails and secure messages;
* preparing proposed replies;
* matter-based message organization;
* privilege and confidentiality prompts;
* attachment review;
* delivery and read-status tracking;
* task creation from communications;
* communication summaries;
* approval before sending;
* preservation within the appropriate matter record.

The system does not autonomously send legally significant communications, make concessions, accept settlements, waive privilege, or communicate with a court, tribunal, opposing party, or client without the required authorization.

## Electronic Document Management

The platform is designed to manage large and complex legal records, including:

* PDFs;
* scanned records;
* photographs;
* audio and video;
* emails;
* contracts;
* court forms;
* tribunal records;
* transcripts;
* financial documents;
* medical records;
* government correspondence;
* spreadsheets and presentations.

Documents are processed through a controlled ingestion workflow that may include:

* encrypted quarantine;
* malware scanning;
* file validation;
* cryptographic hashing;
* OCR and text extraction;
* metadata and EXIF extraction;
* duplicate detection;
* document classification;
* privilege screening;
* page-level indexing;
* source-linked evidence extraction;
* human review of low-confidence results.

Original files are preserved separately from OCR text, summaries, annotations, embeddings, and other derived materials.

## Evidence and Matter Organization

The Evidence Matrix links every material proposition to its supporting or contradicting source.

The platform can organize:

* facts;
* allegations;
* admissions;
* assumptions;
* inferences;
* legal arguments;
* procedural history;
* witnesses;
* events;
* issues;
* remedies;
* authorities;
* deadlines;
* evidentiary gaps.

It can also identify:

* contradictory statements;
* conflicting dates;
* inconsistent addresses;
* missing evidence;
* corroborating records;
* disputed facts;
* unverified quotations;
* evidentiary weaknesses;
* procedural deficiencies;
* unresolved privilege questions.

Every significant factual statement should be traceable to a document, page, paragraph, image, or media timestamp.

## Physical File Management

The platform may also support the organization of physical records through:

* barcode or QR-code labels;
* box and binder identifiers;
* shelf and storage-location records;
* document check-in and check-out;
* scanning queues;
* chain-of-custody entries;
* physical-to-digital record links;
* exhibit and tab numbering;
* destruction and retention tracking.

This allows a user to identify both the electronic record and the physical location of the corresponding original.

## Legal Research and Citation Verification

The legal knowledge system is designed to retrieve and maintain:

* current and historical BC statutes;
* regulations;
* court rules;
* tribunal rules;
* RTB Policy Guidelines;
* official forms;
* BC Supreme Court and Court of Appeal decisions;
* Supreme Court of Canada authorities;
* relevant tribunal decisions;
* point-in-time law.

BC statutory text is verified against the official BC Laws source. Judicial authorities are checked for existence, court level, citation, pinpoint support, appellate history, treatment, jurisdiction, and binding weight.

Unverified or rejected authorities are blocked from court-ready output.

## Human Supervision and Professional Controls

BC Legal AI Associate is a legal research, evidence-analysis, administrative, and drafting-support platform. It is not itself a licensed lawyer and must not be represented as one.

The platform is designed to operate under clear human supervision and includes controls for:

* lawyer competency;
* conflicts;
* client consent;
* privilege;
* confidentiality;
* legal-source verification;
* deadline confirmation;
* procedural compliance;
* document approval;
* production and disclosure;
* audit history.

The system proposes, organizes, checks, and drafts. Qualified humans retain responsibility for professional judgment, legal advice, filing, service, signing, disclosure, negotiation, and representation.

## Platform Availability

The completed platform is intended to be available through:

* Windows desktop application;
* macOS desktop application;
* Android application;
* iPhone and iPad application;
* secure web portal;
* installable Progressive Web App.

All approved applications will connect to the same secure backend while enforcing the same matter isolation, consent, privilege, evidence, citation, and approval requirements.

See `docs/SECTION_G_PLATFORM_AND_DISTRIBUTION.md` and `docs/INSTALLABLE_CLIENT_STATUS.md`.

## Product Outcome

The purpose of BC Legal AI Associate is to create a more organized and defensible legal workflow by bringing together:

* matter management;
* legal drafting;
* legal research;
* evidence analysis;
* calendaring;
* communications;
* electronic records;
* physical records;
* procedural checks;
* human approvals.

The intended result is not autonomous legal practice. It is a supervised legal-work platform that reduces repetitive administrative work, strengthens source verification, improves record organization, and helps legal professionals and authorized users work with greater efficiency, consistency, and accountability.
