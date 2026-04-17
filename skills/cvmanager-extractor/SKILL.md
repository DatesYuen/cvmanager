---
name: cvmanager-extractor
description: Extract structured academic CV content from the CV Manager system. Use when Codex or another AI agent needs to read person profiles, approved items, pending review items, attachments, export outputs, or AI-reviewable raw text from this project. Use for tasks such as exporting resumes, reading approved academic records, reviewing pending extracted content, or downloading item attachments from the local CV Manager APIs and database-backed routes.
---

# CV Manager Extractor

Use this skill to read structured content from the local CV Manager application.

## Workflow

1. Start from the relevant local API instead of scraping UI text.
2. Use approved-content endpoints when the task needs clean published data.
3. Use review endpoints when the task needs raw extracted text, confidence, AI-review status, or editable structured drafts.
4. Use attachment endpoints only after identifying the target `entity_type` and `entity_id`.

## Primary Sources

Use these routes first:

- Approved showcase data:
  `GET /api/showcase/persons`
  `GET /api/showcase/persons/{person_id}`
  `GET /api/showcase/attachments?entity_type=...&entity_id=...`
  `GET /api/showcase/attachments/download/{attachment_id}`

- Pending review data:
  `GET /api/reviews/pending/{person_id}`
  This returns:
  `raw_text`
  structured fields for the entity
  `confidence`
  `ai_review_status`
  `ai_review_message`
  helper fields such as `authors_text` or `applicants_text` when applicable

- Person basics:
  `GET /api/persons/`
  `GET /api/persons/{person_id}`
  `GET /api/profile/{person_id}`
  `GET /api/profile/{person_id}/educations`
  `GET /api/profile/{person_id}/work-experiences`

- Entity-level CRUD/listing:
  `GET /api/{entity_type}/?person_id={person_id}`
  Common entity types:
  `papers`
  `projects`
  `awards`
  `patents`
  `software_copyrights`
  `student_awards`
  `conferences`
  `special_issues`
  `academic_roles`
  `academic_reports`
  `teaching_platforms`
  `industry_standards`

## Data Semantics

Treat these as the canonical meanings:

- `review_status == approved`
  Human-approved content.

- `review_status == pending`
  Extracted content that still needs manual confirmation.

- `confidence`
  Current extraction confidence. This may be rule-based or AI-refreshed.

- `ai_review_status`
  `not_reviewed`, `success`, or `failed` for the latest AI review attempt on a pending item.

- `authors`
  Paper author list with:
  `name`
  `order`
  `is_first_author`
  `is_corresponding_author`

- `authors_text`
  Editable comma-separated paper author string used during review.

- `applicants`
  Patent applicant list.

- `applicants_text`
  Editable comma-separated patent applicant string used during review.

## Recommended Extraction Paths

### Read a clean published resume

1. Call `GET /api/showcase/persons/{person_id}`.
2. Read:
   `person`
   `profile`
   `educations`
   `work_experiences`
   `items`
3. Use per-item `attachments` if files matter.

### Review low-confidence extracted content

1. Call `GET /api/reviews/pending/{person_id}`.
2. For each entity group, use:
   `raw_text` as source text
   structured fields as current extraction result
   `confidence` and `ai_review_status` as review signals

### Download attachments for an approved item

1. Identify the item from showcase data.
2. Read `attachments` from the item if already present.
3. Download with `GET /api/showcase/attachments/download/{attachment_id}`.

## Export-Aware Notes

When the task is about exported documents:

- Use `/api/export/items` for:
  JSON
  Excel
  single-entity DOCX exports
  full resume DOCX/PDF exports

- For full resume export, `entity_type` may be empty and `person_id` is required.

## Practical Guidance

- Prefer showcase endpoints for end-user-visible facts.
- Prefer review endpoints for extraction diagnostics and AI-review workflows.
- Do not infer approval from confidence alone. Use `review_status`.
- Do not assume attachments exist for every item.
- When a task needs the current person identity, use both `name` and `name_en`.
