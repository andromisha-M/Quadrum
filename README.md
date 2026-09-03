# Quadrum — Project Expense Processing (n8n)

Automated expense extraction for project folders in Google Drive, running entirely
on your own hardware: n8n orchestrates, a local Qwen model reads the documents, and
a small helper container turns unreadable PDFs into page images.

| File | What it is |
| --- | --- |
| `quadrum-expense-workflow.json` | The workflow to import into your local n8n |
| `n8n-pdf-render-helper/` | Small PDF → PNG service (the container in your screenshot) |
| `build-workflow.py` | Generator that produces the JSON — easier to edit than 126 KB of JSON if you want structural changes |

---

## What the workflow does

1. **Watches** a root folder in Google Drive. Dropping a folder in it starts a run;
   the folder's name is the project name used everywhere downstream.
2. **Creates**, inside the project folder:
   - `<Project> - PROCESSED` — holds `<Project>.xlsx`, `<Project>.md`, and a
     `Processed Invoices` subfolder
   - `<Project> - UNCOMPLETED` — anything that could not be processed with certainty
3. **Finds every document** in the project folder and its subfolders (4 levels deep),
   skipping the two folders it just created.
4. **Processes them one at a time**, routed by file type:
   - **PDF** → extract the text layer. If the text is good, the LLM structures it.
     If the text is thin or missing (a scan), the PDF is sent to the render helper
     and the **page images** go to the vision model instead.
   - **Image** → straight to the vision model.
   - **Spreadsheet / document** → text extraction, then the LLM.
   - **Anything else** → flagged for manual review, untouched.
5. **Double-checks itself.** Every extraction returns a self-assessed confidence.
   Below the threshold (default 90%), it runs a **second pass** — a stricter prompt
   for text, page images for PDFs — then compares the two. If the passes disagree on
   the amounts, confidence is forced below the threshold and the file is flagged.
6. **Writes a row per expense** to `<Project>.xlsx` and a detailed entry to
   `<Project>.md`, then moves the file to `Processed Invoices` (success) or
   `<Project> - UNCOMPLETED` (needs review).
7. **Finishes** by appending a summary paragraph (row count, net/VAT/gross totals,
   which files need review) to the `.md` and sending you a Telegram message:
   `Processing of the project <name> has finished.`

**Spreadsheet columns**, exactly as specified:

| Seller / Service Provider | Description | Net Cost | VAT | Date |
| --- | --- | --- | --- | --- |
| ACME d.o.o. | Office chairs and desks | 150000000,00 | 33000000,00 | 14.03.2025 |

Amounts are written as text in the `150000000,00` format — no thousands separators,
comma before the cents — so no locale setting can reformat them behind your back.

Anything uncertain stays **out** of the spreadsheet: low-confidence extractions are
logged in the `.md` with a best-guess reading (clearly marked as not written to the
sheet) and the file goes to UNCOMPLETED. The spreadsheet is meant to be trustworthy
without re-checking it.

---

## Setup

### 1. The PDF render helper

Needed for scanned PDFs. It uses PyMuPDF, which ships prebuilt wheels — no poppler
or other system packages, so it runs on a plain `python:3.11-slim` container.

**Option A — docker compose (simplest):**

```bash
cd n8n-pdf-render-helper
docker compose up -d --build
curl http://10.0.1.11:18880/health     # -> {"status":"ok", ...}
```

**Option B — the custom-app form from your screenshot** (image `python`, tag
`3.11-slim`, container port `18880`, which already matches):

- **Volume:** host `<path>/n8n-pdf-render-helper` → container `/app`
- **Command / Post Arguments** (usually under an "advanced" or "extra parameters"
  toggle further down that form):
  ```
  sh -c "pip install --no-cache-dir -r /app/requirements.txt && python -m uvicorn app:app --app-dir /app --host 0.0.0.0 --port 18880"
  ```
- Keep the host port at `18880` so the workflow's default URL works unchanged.

If that form has no command field at all, use Option A — the container image ships
its own start command and needs no overrides.

Sanity check once it's up:

```bash
curl -F "file=@some-invoice.pdf" http://10.0.1.11:18880/pdf-to-images | head -c 300
```

### 2. Import the workflow

n8n → **Workflows → Import from File** → `quadrum-expense-workflow.json`.

### 3. Fill in `Project Config`

One node holds every setting. Open it and set:

| Field | Value |
| --- | --- |
| `rootFolderId` | Google Drive ID of the folder you drop project folders into |
| `telegramChatId` | Your Telegram chat ID |
| `llmApiUrl` | `http://10.0.1.11:18080/v1/chat/completions` (pre-filled) |
| `llmModel` | The model name your llama.cpp server reports at `/v1/models` |
| `pdfRenderHelperUrl` | `http://10.0.1.11:18880/pdf-to-images-base64` (pre-filled) |
| `confidenceThreshold` | `90` — raise it to be stricter, lower to let more through |

The folder ID is the last part of the folder's URL:
`https://drive.google.com/drive/folders/`**`1AbC...xyz`**

Also open **`Trigger - New Project Folder Dropped`** and pick the same root folder
there — trigger nodes need a literal folder, they can't read it from Config.

### 4. Attach credentials

- **Google Drive OAuth2** on every Google Drive node (set it on one, n8n offers it
  on the rest)
- **Telegram API** (bot token) on `Send Telegram Completion`
- The HTTP Request nodes hit your LAN and need no credentials. If your llama.cpp
  server requires an API key, add an `Authorization` header on the three
  `LLM - ...` nodes.

### 5. Test before activating

Run it manually against a small project folder with two or three invoices — one
clean PDF, one scan, one photo — and watch which branch each file takes. Then
activate the workflow so the trigger starts polling (every minute).

---

## Verify these three things after import

n8n's node schemas shift between versions, and this file was written without access
to your instance. All three are quick to confirm, and there are sticky notes on the
canvas at each spot:

1. **`Process Files One By One`** — confirm which output is *done* and which is
   *loop* in your version. As wired: output 1 → `Route - Is PDF?` (the loop body),
   output 0 → `Merge Finalize Entry` (the end). If your node labels them the other
   way round, swap the two lines.
2. **Google Drive nodes** — open each once. Anything n8n wants re-picked shows in red.
3. **`Extract from File` nodes** — confirm the Operation dropdown reads PDF /
   Spreadsheet / Text respectively for your version.

`Extract Document Text` is the one genuinely uncertain piece: not every n8n version
can pull text out of modern `.docx`. If yours can't, those files fail gracefully —
they land in UNCOMPLETED with an explanatory note rather than producing a wrong row.

---

## How it's laid out

The canvas reads left to right in bands, each node doing one thing so you can change
a single step without unpicking the rest:

```
Setup            trigger → config → create folders → create .md
Discovery        list root → levels 1-3 → merge → classify → loop
Per file         route by type → extract → LLM pass 1 → confident?
                   ├─ yes → success
                   └─ no  → PDF? → render pages → vision model
                            else → stricter second text pass
                                   → compare passes → confident?
Success          format row → read .xlsx → append → write .xlsx
                 → append to .md → move to Processed Invoices → next file
Failure          append reason to .md → move to UNCOMPLETED → next file
Finish           totals → summary paragraph in .md → Telegram
```

The workflow re-reads the `.xlsx` from Drive before each append, so it is safe to
stop a run and restart it — and re-running on a project folder that already has a
`PROCESSED` folder exits immediately instead of duplicating the setup.

## Adapting it

- **Different columns** — edit `Format Rows For Spreadsheet` (builds the row) and the
  `COLUMNS` list in `Combine Rows` (preserves existing rows). Change both.
- **Different number format** — the `fmt()` function in `Format Rows For Spreadsheet`.
- **Stricter or looser** — `confidenceThreshold` in `Project Config`.
- **Deeper folder nesting** — copy the three `List Level 3 Children` nodes into a
  Level 4 block and wire it exactly like Level 2 → 3.
- **Different prompts** — the three `LLM - ...` nodes each hold their full prompt in
  the JSON body, so you can tune the wording per pass independently.
