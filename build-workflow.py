#!/usr/bin/env python3
"""Generator for the Quadrum expense-processing n8n workflow (single importable JSON)."""
import json, uuid

nodes = []
conn = {}

def uid():
    return str(uuid.uuid4())

def add(node):
    nodes.append(node)
    return node["name"]

def link(src, dst, src_index=0, dst_index=0):
    c = conn.setdefault(src, {"main": []})
    while len(c["main"]) <= src_index:
        c["main"].append([])
    c["main"][src_index].append({"node": dst, "type": "main", "index": dst_index})

# ---------------- node factories ----------------

def sticky(name, content, pos, w=380, h=260, color=None):
    p = {"content": content, "height": h, "width": w}
    if color:
        p["color"] = color
    return add({"parameters": p, "id": uid(), "name": name,
                "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": pos})

def set_node(name, assignments, pos, include_other=True):
    values = [{"id": uid(), "name": k, "value": v, "type": t} for k, v, t in assignments]
    return add({"parameters": {"assignments": {"assignments": values}, "options": {},
                "includeOtherFields": include_other},
                "id": uid(), "name": name, "type": "n8n-nodes-base.set",
                "typeVersion": 3.4, "position": pos})

def code_node(name, js, pos, mode="runOnceForAllItems"):
    return add({"parameters": {"mode": mode, "language": "javaScript", "jsCode": js},
                "id": uid(), "name": name, "type": "n8n-nodes-base.code",
                "typeVersion": 2, "position": pos})

def if_node(name, left_expr, operation, right_value, pos, value_type="string"):
    cond = {"id": uid(), "leftValue": left_expr, "rightValue": right_value,
            "operator": {"type": value_type, "operation": operation}}
    return add({"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "",
                "typeValidation": "loose"}, "conditions": [cond], "combinator": "and"},
                "options": {}}, "id": uid(), "name": name, "type": "n8n-nodes-base.if",
                "typeVersion": 2.2, "position": pos})

def filter_node(name, left_expr, operation, right_value, pos, value_type="string"):
    cond = {"id": uid(), "leftValue": left_expr, "rightValue": right_value,
            "operator": {"type": value_type, "operation": operation}}
    return add({"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "",
                "typeValidation": "loose"}, "conditions": [cond], "combinator": "and"},
                "options": {}}, "id": uid(), "name": name, "type": "n8n-nodes-base.filter",
                "typeVersion": 2.2, "position": pos})

def noop(name, pos):
    return add({"parameters": {}, "id": uid(), "name": name, "type": "n8n-nodes-base.noOp",
                "typeVersion": 1, "position": pos})

def merge_append(name, pos, inputs=2):
    return add({"parameters": {"mode": "append", "numberInputs": inputs}, "id": uid(),
                "name": name, "type": "n8n-nodes-base.merge", "typeVersion": 3.1, "position": pos})

def merge_combine(name, pos, inputs=2):
    return add({"parameters": {"mode": "combine", "combinationMode": "mergeByPosition",
                "numberInputs": inputs, "options": {}}, "id": uid(), "name": name,
                "type": "n8n-nodes-base.merge", "typeVersion": 3.1, "position": pos})

MY_DRIVE = {"__rl": True, "mode": "list", "value": "My Drive", "cachedResultName": "My Drive"}

def gdrive_search(name, query_expr, pos, return_all=True):
    return add({"parameters": {"resource": "fileFolder", "operation": "search",
                "searchMethod": "query", "queryString": query_expr, "returnAll": return_all,
                "filter": {"driveId": dict(MY_DRIVE)}, "options": {}},
                "id": uid(), "name": name, "type": "n8n-nodes-base.googleDrive",
                "typeVersion": 3, "position": pos})

def gdrive_create_folder(name, folder_name_expr, parent_expr, pos):
    return add({"parameters": {"resource": "folder", "operation": "create",
                "name": folder_name_expr, "driveId": dict(MY_DRIVE),
                "folderId": {"__rl": True, "mode": "id", "value": parent_expr},
                "options": {}},
                "id": uid(), "name": name, "type": "n8n-nodes-base.googleDrive",
                "typeVersion": 3, "position": pos})

def gdrive_download(name, file_id_expr, pos):
    return add({"parameters": {"resource": "file", "operation": "download",
                "fileId": {"__rl": True, "mode": "id", "value": file_id_expr},
                "options": {"binaryPropertyName": "data"}},
                "id": uid(), "name": name, "type": "n8n-nodes-base.googleDrive",
                "typeVersion": 3, "position": pos})

def gdrive_upload(name, file_name_expr, parent_expr, pos, binary_prop="data"):
    return add({"parameters": {"resource": "file", "operation": "upload",
                "name": file_name_expr, "inputDataFieldName": binary_prop,
                "driveId": dict(MY_DRIVE),
                "folderId": {"__rl": True, "mode": "id", "value": parent_expr}, "options": {}},
                "id": uid(), "name": name, "type": "n8n-nodes-base.googleDrive",
                "typeVersion": 3, "position": pos})

def gdrive_update_content(name, file_id_expr, pos, binary_prop="data"):
    return add({"parameters": {"resource": "file", "operation": "update",
                "fileId": {"__rl": True, "mode": "id", "value": file_id_expr},
                "changeFileContent": True,
                "inputDataFieldName": binary_prop, "options": {}},
                "id": uid(), "name": name, "type": "n8n-nodes-base.googleDrive",
                "typeVersion": 3, "position": pos})

def gdrive_move(name, file_id_expr, new_parent_expr, pos):
    target = {"__rl": True, "mode": "id", "value": new_parent_expr}
    return add({"parameters": {"resource": "file", "operation": "move",
                "fileId": {"__rl": True, "mode": "id", "value": file_id_expr},
                "driveId": dict(MY_DRIVE),
                "folderId": dict(target), "destinationFolderId": dict(target),
                "options": {}}, "id": uid(), "name": name,
                "type": "n8n-nodes-base.googleDrive", "typeVersion": 3, "position": pos})

def extract_from_file(name, operation, binary_prop, pos, on_error=True):
    node = {"parameters": {"operation": operation, "binaryPropertyName": binary_prop,
            "options": {}}, "id": uid(), "name": name,
            "type": "n8n-nodes-base.extractFromFile", "typeVersion": 1, "position": pos}
    if on_error:
        node["onError"] = "continueRegularOutput"
    return add(node)

def convert_to_file(name, operation, pos, file_name_expr="sheet"):
    return add({"parameters": {"operation": operation,
                "options": {"fileName": file_name_expr}},
                "id": uid(), "name": name, "type": "n8n-nodes-base.convertToFile",
                "typeVersion": 1.1, "position": pos})

def http_llm(name, body_expr, pos):
    return add({"parameters": {
        "method": "POST",
        "url": "={{ $('Project Config').item.json.llmApiUrl }}",
        "sendHeaders": True,
        "headerParameters": {"parameters": [{"name": "Content-Type", "value": "application/json"}]},
        "sendBody": True, "specifyBody": "json", "jsonBody": body_expr,
        "options": {"timeout": 180000}}, "id": uid(), "name": name,
        "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": pos,
        "onError": "continueRegularOutput"})

def telegram_send(name, chat_id_expr, text_expr, pos):
    return add({"parameters": {"resource": "message", "operation": "sendMessage",
                "chatId": chat_id_expr, "text": text_expr,
                "additionalFields": {"appendAttribution": False}},
                "id": uid(), "name": name,
                "type": "n8n-nodes-base.telegram", "typeVersion": 1.2, "position": pos})

def split_in_batches(name, pos, batch_size=1):
    return add({"parameters": {"batchSize": batch_size, "options": {}}, "id": uid(),
                "name": name, "type": "n8n-nodes-base.splitInBatches",
                "typeVersion": 3, "position": pos})

def gdrive_trigger(name, folder_expr, pos):
    return add({"parameters": {
        "pollTimes": {"item": [{"mode": "everyMinute"}]},
        "triggerOn": "specificFolder",
        "folderToWatch": {"__rl": True, "mode": "id", "value": folder_expr},
        "event": "folderCreated",
        "options": {}}, "id": uid(), "name": name,
        "type": "n8n-nodes-base.googleDriveTrigger", "typeVersion": 1, "position": pos})

# FC = Folder Context node name, referenced everywhere after setup
FC = "Folder Context"
CFG = "Project Config"
LOOP = "Process Files One By One"

def http_llm(name, body_expr, pos):
    return add({"parameters": {
        "method": "POST",
        "url": "={{ $('" + FC + "').first().json.llmApiUrl }}",
        "sendHeaders": True,
        "headerParameters": {"parameters": [{"name": "Content-Type", "value": "application/json"}]},
        "sendBody": True, "specifyBody": "json", "jsonBody": body_expr,
        "options": {"timeout": 180000}}, "id": uid(), "name": name,
        "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": pos,
        "onError": "continueRegularOutput"})

TRYPARSE_JS = """function tryParseJsonArray(s) {
  if (!s) return null;
  let cleaned = String(s).trim();
  cleaned = cleaned.replace(/^```(json)?/i, '').replace(/```$/,'').trim();
  const start = cleaned.indexOf('[');
  const end = cleaned.lastIndexOf(']');
  if (start !== -1 && end !== -1 && end > start) cleaned = cleaned.substring(start, end + 1);
  else {
    const os = cleaned.indexOf('{');
    const oe = cleaned.lastIndexOf('}');
    if (os !== -1 && oe !== -1 && oe > os) cleaned = '[' + cleaned.substring(os, oe + 1) + ']';
  }
  try { return JSON.parse(cleaned); } catch (e) { return null; }
}"""

# =====================================================================
# STICKY NOTES
# =====================================================================
sticky("Note - Overview",
"""## Quadrum Expense Processing Workflow

**What it does:** watches a Google Drive root folder. When a new project
folder is dropped in, it creates a PROCESSED and UNCOMPLETED folder, an
.xlsx tracker and a .md report, then walks the project folder (up to 4
levels deep) for invoices/receipts/contracts, extracts the data with a
local LLM (with a 2nd stricter pass when confidence is low), writes rows
to the .xlsx, logs details to the .md, moves each file to "Processed
Invoices" or UNCOMPLETED, and finally sends a Telegram message + writes a
summary paragraph to the .md.

**Before running, open `Project Config` and fill in:**
- rootFolderId — the Google Drive folder to watch for new project folders
- telegramChatId — your Telegram chat id
- llmApiUrl / llmModel — your local llama.cpp server

**Credentials to attach (per node, one-time):** Google Drive OAuth2 on
every Google Drive node, Telegram API on the Telegram node. HTTP Request
nodes calling your local LLM need no auth (LAN endpoint) — add an API key
header yourself if your server requires one.

See the accompanying README for a full setup + troubleshooting checklist.""",
[-3200, -1400], w=520, h=460, color=4)

sticky("Note - Discovery Depth Limit",
"""**Folder discovery goes 4 levels deep** (project root + 3 nested
levels of subfolders), which comfortably covers structures like
`Project/Invoices/2025/January`. If you nest deeper than that, duplicate
the "List Level 3 Children" block (copy its 3 nodes, rename to Level 4)
and wire it the same way as Level 2→3.""",
[-1150, -1750], w=380, h=220, color=5)

sticky("Note - Verify Per Your n8n Version",
"""**Please verify these three things after import (n8n node schemas
shift between versions):**
1. `Loop Over Items` node — confirm which output is "done" vs "loop" in
   your version and swap the two connection lines if inverted.
2. Every `Google Drive` node — open once, the field pickers should
   auto-resolve; re-pick anything shown in red.
3. `Extract from File` nodes — confirm the Operation dropdown matches
   the file type (PDF / Spreadsheet / Text) for your n8n version.

Everything is broken into small single-purpose nodes specifically so any
of this is a 30-second fix rather than a rebuild.""",
[-1150, 2350], w=420, h=280, color=3)

sticky("Note - Text vs Image Extraction",
"""**Text branch** (PDF / spreadsheet / document): extract raw text →
ask the LLM to structure it → if confidence < threshold, ask again with a
stricter re-check prompt → keep whichever pass is better, flag
disagreements.

**Image branch**: since your LLM is vision-capable, images (and any PDF
whose text extraction failed) are sent to it directly as the picture —
same two-pass confidence logic.""",
[-2150, -300], w=360, h=240, color=6)

sticky("Note - PDF Fallback Limitation",
"""Your n8n setup has no shell/Execute Command access, so this workflow
cannot rasterize a low-confidence PDF into an image (that needs
poppler/pdftoppm or an external service). Instead, a low-confidence PDF
gets a **second, stricter LLM text pass** with arithmetic cross-checking
as the redundancy step. If you later add an image-conversion service
reachable over HTTP, splice an HTTP Request node in here (swap point is
the "Check PDF Text Quality" → "Merge Text Sources" link) to send a
rendered page image to the vision LLM instead.""",
[-2650, -700], w=400, h=280, color=6)

print("stickies placed:", len(nodes))

FOLDER_MIME = "application/vnd.google-apps.folder"

def q(expr):
    """Wrap a JS string-building expression as an n8n expression."""
    return "={{ " + expr + " }}"

# =====================================================================
# 1. SETUP
# =====================================================================
gdrive_trigger("Trigger - New Project Folder Dropped",
               "={{ $json.rootFolderId }}", [-2600, -1000])
# The trigger needs a literal folder id; expression placeholders are not
# supported there, so it is set to a placeholder the user replaces.
nodes[-1]["parameters"]["folderToWatch"] = {"__rl": True, "mode": "id",
                                            "value": "PUT_YOUR_ROOT_FOLDER_ID_HERE"}

set_node("Project Config", [
    ("projectName", "={{ $json.name }}", "string"),
    ("projectFolderId", "={{ $json.id }}", "string"),
    ("rootFolderId", "PUT_YOUR_ROOT_FOLDER_ID_HERE", "string"),
    ("telegramChatId", "PUT_YOUR_TELEGRAM_CHAT_ID_HERE", "string"),
    ("llmApiUrl", "http://10.0.1.11:18080/v1/chat/completions", "string"),
    ("llmModel", "qwen3.5-35b-a3b", "string"),
    ("pdfRenderHelperUrl", "http://10.0.1.11:18880/pdf-to-images-base64", "string"),
    ("confidenceThreshold", "={{ 90 }}", "number"),
    ("processedSuffix", " - PROCESSED", "string"),
    ("uncompletedSuffix", " - UNCOMPLETED", "string"),
    ("processedInvoicesName", "Processed Invoices", "string"),
], [-2340, -1000])
link("Trigger - New Project Folder Dropped", "Project Config")

gdrive_search("Search Existing PROCESSED Folder",
    q("\"'\" + $json.projectFolderId + \"' in parents and name = '\" + $json.projectName + $json.processedSuffix + \"' and trashed = false\""),
    [-2080, -1000])
nodes[-1]["alwaysOutputData"] = True
link("Project Config", "Search Existing PROCESSED Folder")

if_node("Already Initialized?", "={{ !!$json.id }}", "true", True, [-1820, -1000], "boolean")
nodes[-1]["parameters"]["conditions"]["conditions"][0]["operator"] = {"type": "boolean", "operation": "true", "singleValue": True}
del nodes[-1]["parameters"]["conditions"]["conditions"][0]["rightValue"]
link("Search Existing PROCESSED Folder", "Already Initialized?")

noop("Stop - Already Initialized", [-1560, -1150])
link("Already Initialized?", "Stop - Already Initialized", 0)

gdrive_create_folder("Create PROCESSED Folder",
    q("$('Project Config').first().json.projectName + $('Project Config').first().json.processedSuffix"),
    q("$('Project Config').first().json.projectFolderId"), [-1560, -950])
link("Already Initialized?", "Create PROCESSED Folder", 1)

gdrive_create_folder("Create UNCOMPLETED Folder",
    q("$('Project Config').first().json.projectName + $('Project Config').first().json.uncompletedSuffix"),
    q("$('Project Config').first().json.projectFolderId"), [-1300, -950])
link("Create PROCESSED Folder", "Create UNCOMPLETED Folder")

gdrive_create_folder("Create Processed Invoices Subfolder",
    q("$('Project Config').first().json.processedInvoicesName"),
    q("$('Create PROCESSED Folder').first().json.id"), [-1040, -950])
link("Create UNCOMPLETED Folder", "Create Processed Invoices Subfolder")

set_node(FC, [
    ("projectName", "={{ $('Project Config').first().json.projectName }}", "string"),
    ("projectFolderId", "={{ $('Project Config').first().json.projectFolderId }}", "string"),
    ("telegramChatId", "={{ $('Project Config').first().json.telegramChatId }}", "string"),
    ("llmApiUrl", "={{ $('Project Config').first().json.llmApiUrl }}", "string"),
    ("llmModel", "={{ $('Project Config').first().json.llmModel }}", "string"),
    ("pdfRenderHelperUrl", "={{ $('Project Config').first().json.pdfRenderHelperUrl }}", "string"),
    ("confidenceThreshold", "={{ $('Project Config').first().json.confidenceThreshold }}", "number"),
    ("processedFolderId", "={{ $('Create PROCESSED Folder').first().json.id }}", "string"),
    ("uncompletedFolderId", "={{ $('Create UNCOMPLETED Folder').first().json.id }}", "string"),
    ("processedInvoicesFolderId", "={{ $('Create Processed Invoices Subfolder').first().json.id }}", "string"),
], [-780, -950], include_other=False)
link("Create Processed Invoices Subfolder", FC)

code_node("Build Initial MD File", r"""const ctx = $('Folder Context').first().json;
const stamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
const text = '# ' + ctx.projectName + ' - Expense Processing Report\n\n'
  + '_Generated: ' + stamp + ' (UTC)_\n\n'
  + 'Every document found in the project folder is logged below: what was read from it,\n'
  + 'how confident the extraction was, and anything a human should double-check.\n\n'
  + '---\n\n'
  + '## Invoice log\n\n';
return [{
  json: { mdText: text },
  binary: {
    data: {
      data: Buffer.from(text, 'utf-8').toString('base64'),
      mimeType: 'text/markdown',
      fileName: ctx.projectName + '.md',
      fileExtension: 'md'
    }
  }
}];""", [-520, -950])
link(FC, "Build Initial MD File")

gdrive_upload("Upload Initial MD File",
    q("$('Folder Context').first().json.projectName + '.md'"),
    q("$('Folder Context').first().json.processedFolderId"), [-260, -950])
link("Build Initial MD File", "Upload Initial MD File")

# =====================================================================
# 2. RECURSIVE-ISH DISCOVERY (root + 3 nested levels)
# =====================================================================
gdrive_search("List Project Root Children",
    q("\"'\" + $('Folder Context').first().json.projectFolderId + \"' in parents and trashed = false\""),
    [0, -950])
nodes[-1]["alwaysOutputData"] = True
link("Upload Initial MD File", "List Project Root Children")

code_node("Remove Tracking Folders", r"""const ctx = $('Folder Context').first().json;
const skip = [ctx.processedFolderId, ctx.uncompletedFolderId, ctx.processedInvoicesFolderId];
return $input.all().filter(item => item.json && item.json.id && !skip.includes(item.json.id));""",
          [260, -950])
link("List Project Root Children", "Remove Tracking Folders")

def level_block(level, source_node, x, y):
    files_name = "L%d Files Only" % level
    folders_name = "L%d Folders Only" % level
    filter_node(files_name, "={{ $json.mimeType }}", "notEquals", FOLDER_MIME, [x, y - 150])
    filter_node(folders_name, "={{ $json.mimeType }}", "equals", FOLDER_MIME, [x, y + 150])
    link(source_node, files_name)
    link(source_node, folders_name)
    return files_name, folders_name

l0_files, l0_folders = level_block(0, "Remove Tracking Folders", 520, -950)

gdrive_search("List Level 1 Children",
    q("\"'\" + $json.id + \"' in parents and trashed = false\""), [780, -800])
link(l0_folders, "List Level 1 Children")
l1_files, l1_folders = level_block(1, "List Level 1 Children", 1040, -800)

gdrive_search("List Level 2 Children",
    q("\"'\" + $json.id + \"' in parents and trashed = false\""), [1300, -650])
link(l1_folders, "List Level 2 Children")
l2_files, l2_folders = level_block(2, "List Level 2 Children", 1560, -650)

gdrive_search("List Level 3 Children",
    q("\"'\" + $json.id + \"' in parents and trashed = false\""), [1820, -500])
link(l2_folders, "List Level 3 Children")
filter_node("L3 Files Only", "={{ $json.mimeType }}", "notEquals", FOLDER_MIME, [2080, -500])
link("List Level 3 Children", "L3 Files Only")

merge_append("Merge All Discovered Files", [2340, -950], inputs=4)
link(l0_files, "Merge All Discovered Files", 0, 0)
link(l1_files, "Merge All Discovered Files", 0, 1)
link(l2_files, "Merge All Discovered Files", 0, 2)
link("L3 Files Only", "Merge All Discovered Files", 0, 3)

code_node("Prepare File Queue", r"""const IMAGE = ['jpg','jpeg','png','webp','gif','bmp','tif','tiff','heic'];
const SHEET = ['xlsx','xls','csv','ods'];
const DOC   = ['docx','doc','rtf','odt','txt','md'];

const items = $input.all().filter(i => i.json && i.json.id);
if (items.length === 0) {
  return [{ json: { hasFiles: false, fileCount: 0 } }];
}
const seen = new Set();
const out = [];
for (const item of items) {
  if (seen.has(item.json.id)) continue;
  seen.add(item.json.id);
  const name = String(item.json.name || '');
  const ext = name.includes('.') ? name.split('.').pop().toLowerCase() : '';
  let category = 'unsupported';
  if (ext === 'pdf') category = 'pdf';
  else if (IMAGE.includes(ext)) category = 'image';
  else if (SHEET.includes(ext)) category = 'spreadsheet';
  else if (DOC.includes(ext)) category = 'document';
  out.push({ json: { id: item.json.id, name: name, mimeType: item.json.mimeType || '',
                     fileExtension: ext, fileCategory: category, hasFiles: true } });
}
return out;""", [2600, -950])
link("Merge All Discovered Files", "Prepare File Queue")

if_node("Any Files Found?", "={{ $json.hasFiles }}", "true", True, [2860, -950], "boolean")
nodes[-1]["parameters"]["conditions"]["conditions"][0]["operator"] = {"type": "boolean", "operation": "true", "singleValue": True}
del nodes[-1]["parameters"]["conditions"]["conditions"][0]["rightValue"]
link("Prepare File Queue", "Any Files Found?")

split_in_batches(LOOP, [3120, -800])
link("Any Files Found?", LOOP, 0)

print("setup + discovery nodes:", len(nodes))

# =====================================================================
# 3. PER-FILE ROUTING  (Loop output 1 = "loop", output 0 = "done")
# =====================================================================
CUR = "$('" + LOOP + "').first().json"

if_node("Route - Is PDF?", "={{ $json.fileCategory }}", "equals", "pdf", [3380, -600])
link(LOOP, "Route - Is PDF?", 1)
if_node("Route - Is Image?", "={{ $json.fileCategory }}", "equals", "image", [3380, -200])
link("Route - Is PDF?", "Route - Is Image?", 1)
if_node("Route - Is Spreadsheet?", "={{ $json.fileCategory }}", "equals", "spreadsheet", [3380, 200])
link("Route - Is Image?", "Route - Is Spreadsheet?", 1)
if_node("Route - Is Document?", "={{ $json.fileCategory }}", "equals", "document", [3380, 600])
link("Route - Is Spreadsheet?", "Route - Is Document?", 1)

# ---------------- PDF branch ----------------
gdrive_download("Download PDF File", "={{ $json.id }}", [3640, -700])
link("Route - Is PDF?", "Download PDF File", 0)

extract_from_file("Extract PDF Text", "pdf", "data", [3900, -700])
link("Download PDF File", "Extract PDF Text")

code_node("Check PDF Text Quality", r"""const f = $('""" + LOOP + r"""').first().json;
const inp = $input.first().json || {};
const text = String(inp.text || '');
const compact = text.replace(/\s+/g, ' ').trim();
const digits = (compact.match(/[0-9]/g) || []).length;
// A usable invoice text layer has a reasonable amount of text AND numbers.
const ok = compact.length >= 80 && digits >= 6;
return [{ json: {
  fileId: f.id, fileName: f.name, mimeType: f.mimeType, fileCategory: f.fileCategory,
  sourceType: 'pdf', text: text, extractionOk: ok,
  extractionNote: ok ? '' : 'PDF has little or no usable text layer (likely a scan) - falling back to page images.'
} }];""", [4160, -700])
link("Extract PDF Text", "Check PDF Text Quality")

if_node("PDF Text Usable?", "={{ $json.extractionOk }}", "true", True, [4420, -700], "boolean")
nodes[-1]["parameters"]["conditions"]["conditions"][0]["operator"] = {"type": "boolean", "operation": "true", "singleValue": True}
del nodes[-1]["parameters"]["conditions"]["conditions"][0]["rightValue"]
link("Check PDF Text Quality", "PDF Text Usable?")

# ---------------- Spreadsheet branch ----------------
gdrive_download("Download Spreadsheet File", "={{ $json.id }}", [3640, 200])
link("Route - Is Spreadsheet?", "Download Spreadsheet File", 0)
extract_from_file("Extract Spreadsheet Rows", "xlsx", "data", [3900, 200])
link("Download Spreadsheet File", "Extract Spreadsheet Rows")
code_node("Stringify Spreadsheet Rows", r"""const f = $('""" + LOOP + r"""').first().json;
const rows = $input.all().map(i => i.json).filter(r => r && Object.keys(r).length > 0);
let text = '';
if (rows.length > 0) {
  const headers = Array.from(new Set(rows.flatMap(r => Object.keys(r))));
  text = headers.join(' | ') + '\n';
  for (const r of rows) {
    text += headers.map(h => (r[h] === undefined || r[h] === null) ? '' : String(r[h])).join(' | ') + '\n';
  }
}
const ok = text.trim().length > 0;
return [{ json: {
  fileId: f.id, fileName: f.name, mimeType: f.mimeType, fileCategory: f.fileCategory,
  sourceType: 'spreadsheet', text: text, extractionOk: ok,
  extractionNote: ok ? '' : 'Spreadsheet contained no readable rows.'
} }];""", [4160, 200])
link("Extract Spreadsheet Rows", "Stringify Spreadsheet Rows")

# ---------------- Document branch ----------------
gdrive_download("Download Document File", "={{ $json.id }}", [3640, 600])
link("Route - Is Document?", "Download Document File", 0)
extract_from_file("Extract Document Text", "text", "data", [3900, 600])
link("Download Document File", "Extract Document Text")
code_node("Check Document Text Quality", r"""const f = $('""" + LOOP + r"""').first().json;
const inp = $input.first().json || {};
const text = String(inp.text || inp.data || '');
const compact = text.replace(/\s+/g, ' ').trim();
const ok = compact.length >= 40;
return [{ json: {
  fileId: f.id, fileName: f.name, mimeType: f.mimeType, fileCategory: f.fileCategory,
  sourceType: 'document', text: text, extractionOk: ok,
  extractionNote: ok ? '' : 'Could not read text out of this document (format may not be supported by the Extract from File node in this n8n version). Needs manual handling.'
} }];""", [4160, 600])
link("Extract Document Text", "Check Document Text Quality")

# ---------------- Unsupported ----------------
code_node("Mark Unsupported File Type", r"""const f = $('""" + LOOP + r"""').first().json;
return [{ json: {
  fileId: f.id, fileName: f.name, mimeType: f.mimeType, fileCategory: f.fileCategory,
  sourceType: 'unsupported', text: '', extractionOk: false,
  extractionNote: 'File type "' + (f.fileExtension || 'unknown') + '" is not handled automatically (supported: PDF, images, spreadsheets, documents).'
} }];""", [3640, 1000])
link("Route - Is Document?", "Mark Unsupported File Type", 1)

# ---------------- Merge text sources ----------------
merge_append("Merge Text Sources", [4680, 200], inputs=4)
link("PDF Text Usable?", "Merge Text Sources", 0, 0)
link("Stringify Spreadsheet Rows", "Merge Text Sources", 0, 1)
link("Check Document Text Quality", "Merge Text Sources", 0, 2)
link("Mark Unsupported File Type", "Merge Text Sources", 0, 3)

if_node("Text Extracted OK?", "={{ $json.extractionOk }}", "true", True, [4940, 200], "boolean")
nodes[-1]["parameters"]["conditions"]["conditions"][0]["operator"] = {"type": "boolean", "operation": "true", "singleValue": True}
del nodes[-1]["parameters"]["conditions"]["conditions"][0]["rightValue"]
link("Merge Text Sources", "Text Extracted OK?")

print("routing + branches:", len(nodes))

# =====================================================================
# 4. LLM PROMPTS
# =====================================================================
SCHEMA = """Return ONLY a JSON array. One object per expense line item (normally exactly one).
Each object must have exactly these keys:
  "seller"      - the seller / service provider company name, as printed
  "description" - what the expense is for, MAXIMUM 10 words
  "net_cost"    - the amount WITHOUT VAT, as a plain number (dot as decimal separator, no thousands separators, no currency)
  "vat"         - the VAT amount as a plain number; 0 if the document has no VAT
  "date"        - the date on the document, formatted DD.MM.YYYY
  "confidence"  - integer 0-100: your honest confidence that EVERY field above is correct and complete
  "notes"       - short note about anything uncertain, missing or worth a human check. If everything is clear write exactly: Processed correctly, no issues found.

Rules:
- If only a gross/total and a VAT rate are shown, compute net_cost = total - vat and say so in notes.
- If a value is genuinely absent, use 0 for numbers or "" for strings, drop confidence below 90 and explain in notes.
- Be strict with confidence: below 90 whenever anything is ambiguous, cut off, blurry or guessed.
- No markdown, no code fences, no text outside the JSON array."""

SYS_TEXT_1 = ("You are a meticulous accounting clerk extracting expense data from the text of an "
              "invoice, receipt, contract or other financial document.\n\n" + SCHEMA)

SYS_TEXT_2 = ("You are re-checking an extraction that came back with LOW CONFIDENCE. Read the text again "
              "very carefully, digit by digit for every number. Verify that net_cost + vat equals any total "
              "printed on the document, and recompute if it does not. Only report confidence 90 or above if "
              "you are genuinely certain of every single field.\n\n" + SCHEMA)

SYS_IMG_1 = ("You are a meticulous accounting clerk reading images of an invoice, receipt or financial "
             "document. Read every number and label carefully from the image(s).\n\n" + SCHEMA)

SYS_IMG_2 = ("You are re-checking an image extraction that came back with LOW CONFIDENCE. Look again very "
             "closely at every digit, the seller name and the date. Verify net_cost + vat against any printed "
             "total. Only report confidence 90 or above if you are genuinely certain of every field.\n\n" + SCHEMA)

def text_body(system_prompt):
    return ("={{ JSON.stringify({ model: $('" + FC + "').first().json.llmModel, temperature: 0.1, "
            "max_tokens: 900, messages: [ { role: 'system', content: " + json.dumps(system_prompt) + " }, "
            "{ role: 'user', content: 'FILE NAME: ' + $json.fileName + '\\n\\nDOCUMENT TEXT:\\n\\n' + "
            "String($json.text).substring(0, 12000) } ] }) }}")

def image_body(system_prompt, user_text):
    return ("={{ JSON.stringify({ model: $('" + FC + "').first().json.llmModel, temperature: 0.1, "
            "max_tokens: 900, messages: [ { role: 'system', content: " + json.dumps(system_prompt) + " }, "
            "{ role: 'user', content: [ { type: 'text', text: " + json.dumps(user_text) + " + ' FILE NAME: ' + $json.fileName } ]"
            ".concat(($json.imageDataUrls || []).map(u => ({ type: 'image_url', image_url: { url: u } }))) } ] }) }}")

PARSE_TMPL = r"""%(tryparse)s
const ctx = $('%(ctx_node)s').first().json;
const resp = $input.first().json || {};
let raw = '';
try { raw = resp.choices[0].message.content; } catch (e) { raw = ''; }
if (!raw && typeof resp.content === 'string') raw = resp.content;
const parsed = tryParseJsonArray(raw);
const entries = Array.isArray(parsed) ? parsed : (parsed ? [parsed] : []);
const clean = entries.filter(e => e && typeof e === 'object');
const valid = clean.length > 0;
const confidence = valid ? Math.min.apply(null, clean.map(e => Number(e.confidence) || 0)) : 0;
return [{ json: Object.assign({}, ctx, {
  %(prefix)sEntries: clean,
  %(prefix)sConfidence: confidence,
  %(prefix)sValid: valid,
  %(prefix)sRaw: String(raw).substring(0, 2000)
}) }];"""

def parse_code(ctx_node, prefix):
    return PARSE_TMPL % {"tryparse": TRYPARSE_JS, "ctx_node": ctx_node, "prefix": prefix}

PICK_BEST = r"""const d = $input.first().json;
const threshold = Number($('""" + FC + r"""').first().json.confidenceThreshold) || 90;
let finalEntries = [], finalConfidence = 0, note = '';
if (d.pass2Valid && Number(d.pass2Confidence) >= Number(d.pass1Confidence || 0)) {
  finalEntries = d.pass2Entries; finalConfidence = Number(d.pass2Confidence);
  note = 'Second (strict re-check) pass used.';
} else if (d.pass1Valid) {
  finalEntries = d.pass1Entries; finalConfidence = Number(d.pass1Confidence);
  note = 'First pass used - the strict re-check did not improve confidence.';
} else {
  note = 'Both extraction passes failed to return usable data.';
}
if (d.pass1Valid && d.pass2Valid && d.pass1Entries.length && d.pass2Entries.length) {
  const a = Number(d.pass1Entries[0].net_cost) || 0;
  const b = Number(d.pass2Entries[0].net_cost) || 0;
  const va = Number(d.pass1Entries[0].vat) || 0;
  const vb = Number(d.pass2Entries[0].vat) || 0;
  if (Math.abs(a - b) > 0.01 || Math.abs(va - vb) > 0.01) {
    note += ' WARNING: the two passes disagree (net ' + a + ' vs ' + b + ', VAT ' + va + ' vs ' + vb + ') - needs a human check.';
    finalConfidence = Math.min(finalConfidence, threshold - 1);
  } else {
    note += ' Both passes agree on the amounts.';
  }
}
return [{ json: Object.assign({}, d, { finalEntries, finalConfidence, finalNote: note }) }];"""

SUCCESS_TMPL = r"""const d = $input.first().json;
const entries = d.%(entries)s || [];
const confidence = Number(d.%(conf)s) || 0;
const extraNote = %(note)s;
return entries.map(e => ({ json: {
  fileId: d.fileId, fileName: d.fileName, sourceType: d.sourceType,
  seller: String(e.seller || ''),
  description: String(e.description || '').split(/\s+/).slice(0, 10).join(' '),
  netCost: Number(e.net_cost) || 0,
  vat: Number(e.vat) || 0,
  invoiceDate: String(e.date || ''),
  confidence: confidence,
  notes: [String(e.notes || ''), extraNote].filter(Boolean).join(' ')
} }));"""

def success_code(entries, conf, note_expr):
    return SUCCESS_TMPL % {"entries": entries, "conf": conf, "note": note_expr}

# =====================================================================
# 5. TEXT LLM CHAIN
# =====================================================================
http_llm("LLM - Extract From Text (Pass 1)", text_body(SYS_TEXT_1), [5200, 100])
link("Text Extracted OK?", "LLM - Extract From Text (Pass 1)", 0)

code_node("Parse LLM Response (Text Pass 1)", parse_code("Text Extracted OK?", "pass1"), [5460, 100])
link("LLM - Extract From Text (Pass 1)", "Parse LLM Response (Text Pass 1)")

if_node("Text Pass 1 Confident?",
        "={{ $json.pass1Valid && $json.pass1Confidence >= $('" + FC + "').first().json.confidenceThreshold }}",
        "true", True, [5720, 100], "boolean")
nodes[-1]["parameters"]["conditions"]["conditions"][0]["operator"] = {"type": "boolean", "operation": "true", "singleValue": True}
del nodes[-1]["parameters"]["conditions"]["conditions"][0]["rightValue"]
link("Parse LLM Response (Text Pass 1)", "Text Pass 1 Confident?")

code_node("Build Success Entries (Text Pass 1)",
          success_code("pass1Entries", "pass1Confidence",
                       "'Read from the document text layer, confident on the first pass.'"),
          [5980, -100])
link("Text Pass 1 Confident?", "Build Success Entries (Text Pass 1)", 0)

if_node("Low Confidence - Is It A PDF?", "={{ $json.sourceType }}", "equals", "pdf", [5980, 300])
link("Text Pass 1 Confident?", "Low Confidence - Is It A PDF?", 1)

http_llm("LLM - Extract From Text (Pass 2 Strict)", text_body(SYS_TEXT_2), [6240, 500])
link("Low Confidence - Is It A PDF?", "LLM - Extract From Text (Pass 2 Strict)", 1)

code_node("Parse LLM Response (Text Pass 2)", parse_code("Low Confidence - Is It A PDF?", "pass2"), [6500, 500])
link("LLM - Extract From Text (Pass 2 Strict)", "Parse LLM Response (Text Pass 2)")

code_node("Pick Best Text Extraction", PICK_BEST, [6760, 500])
link("Parse LLM Response (Text Pass 2)", "Pick Best Text Extraction")

if_node("Text Final Confident?",
        "={{ $json.finalConfidence >= $('" + FC + "').first().json.confidenceThreshold }}",
        "true", True, [7020, 500], "boolean")
nodes[-1]["parameters"]["conditions"]["conditions"][0]["operator"] = {"type": "boolean", "operation": "true", "singleValue": True}
del nodes[-1]["parameters"]["conditions"]["conditions"][0]["rightValue"]
link("Pick Best Text Extraction", "Text Final Confident?")

code_node("Build Success Entries (Text Final)",
          success_code("finalEntries", "finalConfidence", "d.finalNote || ''"), [7280, 400])
link("Text Final Confident?", "Build Success Entries (Text Final)", 0)

print("text chain:", len(nodes))

# =====================================================================
# 6. PDF -> IMAGE FALLBACK (via the local render helper container)
# =====================================================================
merge_append("Merge PDF Fallback Entry", [4680, -900], inputs=2)
link("PDF Text Usable?", "Merge PDF Fallback Entry", 1, 0)
link("Low Confidence - Is It A PDF?", "Merge PDF Fallback Entry", 0, 1)

gdrive_download("Download PDF For Rendering",
                "={{ $('" + LOOP + "').first().json.id }}", [4940, -900])
link("Merge PDF Fallback Entry", "Download PDF For Rendering")

code_node("PDF Binary To Base64", r"""// getBinaryDataBuffer works whether n8n keeps binaries in memory or on disk.
let base64 = '';
try {
  const buffer = await this.helpers.getBinaryDataBuffer(0, 'data');
  base64 = buffer.toString('base64');
} catch (e) {
  base64 = '';
}
return [{ json: { pdfBase64: base64, pdfBytes: base64.length } }];""", [5200, -900])
link("Download PDF For Rendering", "PDF Binary To Base64")

add({"parameters": {
    "method": "POST",
    "url": "={{ $('" + FC + "').first().json.pdfRenderHelperUrl }}",
    "sendHeaders": True,
    "headerParameters": {"parameters": [{"name": "Content-Type", "value": "application/json"}]},
    "sendBody": True, "specifyBody": "json",
    "jsonBody": "={{ JSON.stringify({ base64: $json.pdfBase64, dpi: 200, max_pages: 3 }) }}",
    "options": {"timeout": 120000}},
    "id": uid(), "name": "Render PDF Pages To Images",
    "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [5460, -900],
    "onError": "continueRegularOutput"})
link("PDF Binary To Base64", "Render PDF Pages To Images")

code_node("Build Image Payload From Rendered PDF", r"""const f = $('""" + LOOP + r"""').first().json;
// input is the JSON response from the render helper container

const resp = $input.first().json || {};
const images = Array.isArray(resp.images) ? resp.images : [];
const urls = images.map(img => 'data:' + (img.mimeType || 'image/png') + ';base64,' + img.base64);
return [{ json: {
  fileId: f.id, fileName: f.name, mimeType: f.mimeType, sourceType: 'pdf-rendered',
  imageDataUrls: urls,
  imageOk: urls.length > 0,
  imageNote: urls.length > 0
    ? ('PDF text was unreliable, so ' + urls.length + ' rendered page image(s) were read by the vision model instead.')
    : ('The PDF render helper returned no images (' + (resp.detail || resp.message || 'no response') + '). Check that the helper container is running and reachable.')
} }];""", [5720, -900])
link("Render PDF Pages To Images", "Build Image Payload From Rendered PDF")

# ---------------- Direct image files ----------------
gdrive_download("Download Image File", "={{ $json.id }}", [3640, -200])
link("Route - Is Image?", "Download Image File", 0)

code_node("Build Image Payload From File", r"""const f = $('""" + LOOP + r"""').first().json;
const meta = ($input.first().binary || {}).data || {};
let base64 = '';
try {
  const buffer = await this.helpers.getBinaryDataBuffer(0, 'data');
  base64 = buffer.toString('base64');
} catch (e) {
  base64 = '';
}
const ok = base64.length > 0;
const mime = meta.mimeType || 'image/png';
return [{ json: {
  fileId: f.id, fileName: f.name, mimeType: f.mimeType, sourceType: 'image',
  imageDataUrls: ok ? ['data:' + mime + ';base64,' + base64] : [],
  imageOk: ok,
  imageNote: ok ? 'Image read directly by the vision model.' : 'Could not read the image file contents from Google Drive.'
} }];""", [3900, -200])
link("Download Image File", "Build Image Payload From File")

merge_append("Merge Image Sources", [5720, -500], inputs=2)
link("Build Image Payload From Rendered PDF", "Merge Image Sources", 0, 0)
link("Build Image Payload From File", "Merge Image Sources", 0, 1)

if_node("Image Payload OK?", "={{ $json.imageOk }}", "true", True, [5980, -500], "boolean")
nodes[-1]["parameters"]["conditions"]["conditions"][0]["operator"] = {"type": "boolean", "operation": "true", "singleValue": True}
del nodes[-1]["parameters"]["conditions"]["conditions"][0]["rightValue"]
link("Merge Image Sources", "Image Payload OK?")

# =====================================================================
# 7. IMAGE (VISION) LLM CHAIN
# =====================================================================
http_llm("LLM - Extract From Image (Pass 1)",
         image_body(SYS_IMG_1, "Read this financial document and extract the expense data."),
         [6240, -600])
link("Image Payload OK?", "LLM - Extract From Image (Pass 1)", 0)

code_node("Parse LLM Response (Image Pass 1)", parse_code("Image Payload OK?", "pass1"), [6500, -600])
link("LLM - Extract From Image (Pass 1)", "Parse LLM Response (Image Pass 1)")

if_node("Image Pass 1 Confident?",
        "={{ $json.pass1Valid && $json.pass1Confidence >= $('" + FC + "').first().json.confidenceThreshold }}",
        "true", True, [6760, -600], "boolean")
nodes[-1]["parameters"]["conditions"]["conditions"][0]["operator"] = {"type": "boolean", "operation": "true", "singleValue": True}
del nodes[-1]["parameters"]["conditions"]["conditions"][0]["rightValue"]
link("Parse LLM Response (Image Pass 1)", "Image Pass 1 Confident?")

code_node("Build Success Entries (Image Pass 1)",
          success_code("pass1Entries", "pass1Confidence", "d.imageNote || ''"), [7020, -800])
link("Image Pass 1 Confident?", "Build Success Entries (Image Pass 1)", 0)

http_llm("LLM - Extract From Image (Pass 2 Strict)",
         image_body(SYS_IMG_2, "Re-read this financial document very carefully."), [7020, -400])
link("Image Pass 1 Confident?", "LLM - Extract From Image (Pass 2 Strict)", 1)

code_node("Parse LLM Response (Image Pass 2)", parse_code("Image Pass 1 Confident?", "pass2"), [7280, -400])
link("LLM - Extract From Image (Pass 2 Strict)", "Parse LLM Response (Image Pass 2)")

code_node("Pick Best Image Extraction", PICK_BEST, [7540, -400])
link("Parse LLM Response (Image Pass 2)", "Pick Best Image Extraction")

if_node("Image Final Confident?",
        "={{ $json.finalConfidence >= $('" + FC + "').first().json.confidenceThreshold }}",
        "true", True, [7800, -400], "boolean")
nodes[-1]["parameters"]["conditions"]["conditions"][0]["operator"] = {"type": "boolean", "operation": "true", "singleValue": True}
del nodes[-1]["parameters"]["conditions"]["conditions"][0]["rightValue"]
link("Pick Best Image Extraction", "Image Final Confident?")

code_node("Build Success Entries (Image Final)",
          success_code("finalEntries", "finalConfidence",
                       "((d.imageNote || '') + ' ' + (d.finalNote || '')).trim()"), [8060, -500])
link("Image Final Confident?", "Build Success Entries (Image Final)", 0)

print("image chain:", len(nodes))

# =====================================================================
# 8. FAILURE REASONS
# =====================================================================
FAIL_TMPL = r"""const d = $input.first().json;
const threshold = $('""" + FC + r"""').first().json.confidenceThreshold;
return [{ json: {
  fileId: d.fileId, fileName: d.fileName, sourceType: d.sourceType || 'unknown',
  bestGuess: %(guess)s,
  reason: %(reason)s
} }];"""

code_node("Failure - Could Not Read File", FAIL_TMPL % {
    "guess": "null",
    "reason": "d.extractionNote || 'The file could not be read for processing.'"},
    [5200, 700])
link("Text Extracted OK?", "Failure - Could Not Read File", 1)

code_node("Failure - Low Confidence (Text)", FAIL_TMPL % {
    "guess": "(d.finalEntries && d.finalEntries.length) ? d.finalEntries[0] : null",
    "reason": "'Two extraction passes could not reach ' + threshold + '% confidence (best was ' + d.finalConfidence + '%). ' + (d.finalNote || '')"},
    [7280, 700])
link("Text Final Confident?", "Failure - Low Confidence (Text)", 1)

code_node("Failure - No Usable Images", FAIL_TMPL % {
    "guess": "null",
    "reason": "d.imageNote || 'No page images could be produced for this file.'"},
    [6240, -200])
link("Image Payload OK?", "Failure - No Usable Images", 1)

code_node("Failure - Low Confidence (Image)", FAIL_TMPL % {
    "guess": "(d.finalEntries && d.finalEntries.length) ? d.finalEntries[0] : null",
    "reason": "'Two vision passes could not reach ' + threshold + '% confidence (best was ' + d.finalConfidence + '%). ' + (d.finalNote || '')"},
    [8060, -200])
link("Image Final Confident?", "Failure - Low Confidence (Image)", 1)

merge_append("Merge Failure Paths", [8320, 400], inputs=4)
link("Failure - Could Not Read File", "Merge Failure Paths", 0, 0)
link("Failure - Low Confidence (Text)", "Merge Failure Paths", 0, 1)
link("Failure - No Usable Images", "Merge Failure Paths", 0, 2)
link("Failure - Low Confidence (Image)", "Merge Failure Paths", 0, 3)

merge_append("Merge Success Paths", [8320, -700], inputs=4)
link("Build Success Entries (Text Pass 1)", "Merge Success Paths", 0, 0)
link("Build Success Entries (Text Final)", "Merge Success Paths", 0, 1)
link("Build Success Entries (Image Pass 1)", "Merge Success Paths", 0, 2)
link("Build Success Entries (Image Final)", "Merge Success Paths", 0, 3)

print("failure/success merges:", len(nodes))

# =====================================================================
# 9. SUCCESS CONVERGENCE - write rows to the project .xlsx
# =====================================================================
code_node("Format Rows For Spreadsheet", r"""// Amounts are written exactly as asked: no thousands separator, comma before the cents.
function fmt(value) {
  const num = Number(value) || 0;
  const parts = Math.abs(num).toFixed(2).split('.');
  return (num < 0 ? '-' : '') + parts[0] + ',' + parts[1];
}
const items = $input.all().map(i => i.json);
const newRows = items.map(e => ({
  'Seller / Service Provider': e.seller || '',
  'Description': e.description || '',
  'Net Cost': fmt(e.netCost),
  'VAT': fmt(e.vat),
  'Date': e.invoiceDate || ''
}));
const first = items[0] || {};
return [{ json: {
  fileId: first.fileId, fileName: first.fileName, sourceType: first.sourceType,
  confidence: first.confidence, notes: items.map(i => i.notes).filter(Boolean).join(' | '),
  entryCount: newRows.length,
  netTotal: items.reduce((s, i) => s + (Number(i.netCost) || 0), 0),
  vatTotal: items.reduce((s, i) => s + (Number(i.vat) || 0), 0),
  newRows: newRows
} }];""", [8580, -700])
link("Merge Success Paths", "Format Rows For Spreadsheet")

gdrive_search("Search Project XLSX",
    q("\"'\" + $('" + FC + "').first().json.processedFolderId + \"' in parents and name = '\" + $('" + FC + "').first().json.projectName + \".xlsx' and trashed = false\""),
    [8840, -700])
nodes[-1]["alwaysOutputData"] = True
link("Format Rows For Spreadsheet", "Search Project XLSX")

if_node("XLSX Exists?", "={{ !!$json.id }}", "true", True, [9100, -700], "boolean")
nodes[-1]["parameters"]["conditions"]["conditions"][0]["operator"] = {"type": "boolean", "operation": "true", "singleValue": True}
del nodes[-1]["parameters"]["conditions"]["conditions"][0]["rightValue"]
link("Search Project XLSX", "XLSX Exists?")

gdrive_download("Download Existing XLSX", "={{ $json.id }}", [9360, -850])
link("XLSX Exists?", "Download Existing XLSX", 0)
extract_from_file("Extract Existing XLSX Rows", "xlsx", "data", [9620, -850])
link("Download Existing XLSX", "Extract Existing XLSX Rows")

code_node("No Existing Rows", "return [{ json: { __placeholder: true } }];", [9360, -550])
link("XLSX Exists?", "No Existing Rows", 1)

merge_append("Merge Existing Rows", [9880, -700], inputs=2)
link("Extract Existing XLSX Rows", "Merge Existing Rows", 0, 0)
link("No Existing Rows", "Merge Existing Rows", 0, 1)

code_node("Combine Rows", r"""const COLUMNS = ['Seller / Service Provider', 'Description', 'Net Cost', 'VAT', 'Date'];
const existing = $input.all()
  .map(i => i.json)
  .filter(r => r && !r.__placeholder && Object.keys(r).length > 0)
  .map(r => {
    const row = {};
    for (const c of COLUMNS) row[c] = r[c] === undefined || r[c] === null ? '' : String(r[c]);
    return row;
  });
const newRows = $('Format Rows For Spreadsheet').first().json.newRows || [];
return existing.concat(newRows).map(row => ({ json: row }));""", [10140, -700])
link("Merge Existing Rows", "Combine Rows")

convert_to_file("Convert Rows To XLSX", "xlsx", [10400, -700],
                q("$('" + FC + "').first().json.projectName + '.xlsx'"))
link("Combine Rows", "Convert Rows To XLSX")

if_node("XLSX Existed Before?", "={{ !!$('Search Project XLSX').first().json.id }}", "true", True,
        [10660, -700], "boolean")
nodes[-1]["parameters"]["conditions"]["conditions"][0]["operator"] = {"type": "boolean", "operation": "true", "singleValue": True}
del nodes[-1]["parameters"]["conditions"]["conditions"][0]["rightValue"]
link("Convert Rows To XLSX", "XLSX Existed Before?")

gdrive_update_content("Update Project XLSX",
                      "={{ $('Search Project XLSX').first().json.id }}", [10920, -850])
link("XLSX Existed Before?", "Update Project XLSX", 0)

gdrive_upload("Create Project XLSX",
              q("$('" + FC + "').first().json.projectName + '.xlsx'"),
              q("$('" + FC + "').first().json.processedFolderId"), [10920, -550])
link("XLSX Existed Before?", "Create Project XLSX", 1)

merge_append("Merge After XLSX Write", [11180, -700], inputs=2)
link("Update Project XLSX", "Merge After XLSX Write", 0, 0)
link("Create Project XLSX", "Merge After XLSX Write", 0, 1)

gdrive_download("Download MD (Success)",
                "={{ $('Upload Initial MD File').first().json.id }}", [11440, -700])
link("Merge After XLSX Write", "Download MD (Success)")

MD_APPEND_HEAD = r"""let current = '';
try {
  const buffer = await this.helpers.getBinaryDataBuffer(0, 'data');
  current = buffer.toString('utf-8');
} catch (e) {
  current = '';
}
const ctx = $('""" + FC + r"""').first().json;
if (!current) {
  current = '# ' + ctx.projectName + ' - Expense Processing Report\n\n## Invoice log\n\n';
}
"""

MD_APPEND_TAIL = r"""
const updated = current + entry;
return [{
  json: { mdLength: updated.length },
  binary: { data: {
    data: Buffer.from(updated, 'utf-8').toString('base64'),
    mimeType: 'text/markdown',
    fileName: ctx.projectName + '.md',
    fileExtension: 'md'
  } }
}];"""

code_node("Append Success Entry To MD", MD_APPEND_HEAD + r"""const d = $('Format Rows For Spreadsheet').first().json;
const rows = d.newRows || [];
let entry = '### ' + d.fileName + '\n\n';
entry += '- **Status:** processed (' + d.confidence + '% confidence)\n';
entry += '- **Read as:** ' + d.sourceType + '\n';
for (const r of rows) {
  entry += '- **Row written:** ' + r['Seller / Service Provider'] + ' | ' + r['Description']
        + ' | net ' + r['Net Cost'] + ' | VAT ' + r['VAT'] + ' | ' + r['Date'] + '\n';
}
entry += '- **Notes:** ' + (d.notes || 'Processed correctly, no issues found.') + '\n';
entry += '- **Moved to:** ' + ctx.projectName + ' - PROCESSED / Processed Invoices\n\n';
""" + MD_APPEND_TAIL, [11700, -700])
link("Download MD (Success)", "Append Success Entry To MD")

gdrive_update_content("Update MD File (Success)",
                      "={{ $('Upload Initial MD File').first().json.id }}", [11960, -700])
link("Append Success Entry To MD", "Update MD File (Success)")

gdrive_move("Move File To Processed Invoices",
            "={{ $('" + LOOP + "').first().json.id }}",
            "={{ $('" + FC + "').first().json.processedInvoicesFolderId }}", [12220, -700])
link("Update MD File (Success)", "Move File To Processed Invoices")
link("Move File To Processed Invoices", LOOP)

# =====================================================================
# 10. FAILURE CONVERGENCE - log it and move the file to UNCOMPLETED
# =====================================================================
gdrive_download("Download MD (Failure)",
                "={{ $('Upload Initial MD File').first().json.id }}", [8580, 400])
link("Merge Failure Paths", "Download MD (Failure)")

code_node("Append Failure Entry To MD", MD_APPEND_HEAD + r"""const d = $('Merge Failure Paths').first().json;
let entry = '### ' + d.fileName + '  -  NEEDS MANUAL REVIEW\n\n';
entry += '- **Status:** NOT processed\n';
entry += '- **Read as:** ' + (d.sourceType || 'unknown') + '\n';
entry += '- **Reason:** ' + (d.reason || 'Unknown problem.') + '\n';
if (d.bestGuess) {
  entry += '- **Best guess (NOT written to the spreadsheet):** '
        + (d.bestGuess.seller || '?') + ' | ' + (d.bestGuess.description || '?')
        + ' | net ' + (d.bestGuess.net_cost !== undefined ? d.bestGuess.net_cost : '?')
        + ' | VAT ' + (d.bestGuess.vat !== undefined ? d.bestGuess.vat : '?')
        + ' | ' + (d.bestGuess.date || '?') + '\n';
}
entry += '- **Moved to:** ' + ctx.projectName + ' - UNCOMPLETED\n\n';
""" + MD_APPEND_TAIL, [8840, 400])
link("Download MD (Failure)", "Append Failure Entry To MD")

gdrive_update_content("Update MD File (Failure)",
                      "={{ $('Upload Initial MD File').first().json.id }}", [9100, 400])
link("Append Failure Entry To MD", "Update MD File (Failure)")

gdrive_move("Move File To UNCOMPLETED",
            "={{ $('" + LOOP + "').first().json.id }}",
            "={{ $('" + FC + "').first().json.uncompletedFolderId }}", [9360, 400])
link("Update MD File (Failure)", "Move File To UNCOMPLETED")
link("Move File To UNCOMPLETED", LOOP)

print("convergence:", len(nodes))

# =====================================================================
# 11. FINALIZE - summary paragraph + Telegram
# =====================================================================
merge_append("Merge Finalize Entry", [3380, 1500], inputs=2)
link(LOOP, "Merge Finalize Entry", 0, 0)
link("Any Files Found?", "Merge Finalize Entry", 1, 1)

gdrive_search("Search Final XLSX",
    q("\"'\" + $('" + FC + "').first().json.processedFolderId + \"' in parents and name = '\" + $('" + FC + "').first().json.projectName + \".xlsx' and trashed = false\""),
    [3640, 1500])
nodes[-1]["alwaysOutputData"] = True
link("Merge Finalize Entry", "Search Final XLSX")

if_node("Final XLSX Exists?", "={{ !!$json.id }}", "true", True, [3900, 1500], "boolean")
nodes[-1]["parameters"]["conditions"]["conditions"][0]["operator"] = {"type": "boolean", "operation": "true", "singleValue": True}
del nodes[-1]["parameters"]["conditions"]["conditions"][0]["rightValue"]
link("Search Final XLSX", "Final XLSX Exists?")

gdrive_download("Download Final XLSX", "={{ $json.id }}", [4160, 1350])
link("Final XLSX Exists?", "Download Final XLSX", 0)
extract_from_file("Extract Final Rows", "xlsx", "data", [4420, 1350])
link("Download Final XLSX", "Extract Final Rows")

code_node("No Final Rows", "return [{ json: { __placeholder: true } }];", [4160, 1650])
link("Final XLSX Exists?", "No Final Rows", 1)

merge_append("Merge Final Rows", [4680, 1500], inputs=2)
link("Extract Final Rows", "Merge Final Rows", 0, 0)
link("No Final Rows", "Merge Final Rows", 0, 1)

code_node("Collect Final Rows", r"""function parseAmount(v) {
  if (v === undefined || v === null) return 0;
  return Number(String(v).replace(/\./g, '').replace(',', '.')) || 0;
}
const rows = $input.all().map(i => i.json).filter(r => r && !r.__placeholder && r['Seller / Service Provider'] !== undefined);
const netTotal = rows.reduce((s, r) => s + parseAmount(r['Net Cost']), 0);
const vatTotal = rows.reduce((s, r) => s + parseAmount(r['VAT']), 0);
return [{ json: { rowCount: rows.length, netTotal, vatTotal, grossTotal: netTotal + vatTotal } }];""",
          [4940, 1500])
link("Merge Final Rows", "Collect Final Rows")

gdrive_search("List UNCOMPLETED Files",
    q("\"'\" + $('" + FC + "').first().json.uncompletedFolderId + \"' in parents and trashed = false\""),
    [5200, 1500])
nodes[-1]["alwaysOutputData"] = True
link("Collect Final Rows", "List UNCOMPLETED Files")

code_node("Collect Uncompleted Files", r"""const files = $input.all().map(i => i.json).filter(f => f && f.id);
return [{ json: { uncompletedCount: files.length, uncompletedNames: files.map(f => f.name) } }];""",
          [5460, 1500])
link("List UNCOMPLETED Files", "Collect Uncompleted Files")

gdrive_download("Download MD (Final)",
                "={{ $('Upload Initial MD File').first().json.id }}", [5720, 1500])
link("Collect Uncompleted Files", "Download MD (Final)")

code_node("Append Summary To MD", MD_APPEND_HEAD + r"""function fmt(num) {
  const parts = Math.abs(Number(num) || 0).toFixed(2).split('.');
  return ((Number(num) || 0) < 0 ? '-' : '') + parts[0] + ',' + parts[1];
}
const totals = $('Collect Final Rows').first().json;
const unc = $('Collect Uncompleted Files').first().json;
const stamp = new Date().toISOString().replace('T', ' ').substring(0, 19);

let entry = '\n---\n\n## Summary\n\n';
entry += 'Processing of **' + ctx.projectName + '** finished on ' + stamp + ' (UTC). ';
entry += 'A total of **' + totals.rowCount + ' expense row(s)** were written to `' + ctx.projectName + '.xlsx`, ';
entry += 'adding up to a net total of **' + fmt(totals.netTotal) + '**, VAT of **' + fmt(totals.vatTotal) + '**, ';
entry += 'and a gross total of **' + fmt(totals.grossTotal) + '**. ';
if (unc.uncompletedCount > 0) {
  entry += '**' + unc.uncompletedCount + ' file(s) could not be processed with enough certainty** and were moved to the '
        + ctx.projectName + ' - UNCOMPLETED folder: ' + unc.uncompletedNames.join(', ') + '. '
        + 'Each of them is listed above with the reason it failed, so they can be entered by hand or re-run after a fix. ';
} else {
  entry += 'Every document found in the project folder was processed successfully, with no files left for manual review. ';
}
entry += 'All figures above come straight from the rows written to the spreadsheet, so the spreadsheet remains the single source of truth.\n';
""" + MD_APPEND_TAIL, [5980, 1500])
link("Download MD (Final)", "Append Summary To MD")

gdrive_update_content("Update MD File (Final)",
                      "={{ $('Upload Initial MD File').first().json.id }}", [6240, 1500])
link("Append Summary To MD", "Update MD File (Final)")

telegram_send("Send Telegram Completion",
              "={{ $('" + FC + "').first().json.telegramChatId }}",
              "={{ 'Processing of the project ' + $('" + FC + "').first().json.projectName + ' has finished.' }}",
              [6500, 1500])
link("Update MD File (Final)", "Send Telegram Completion")

# =====================================================================
# 12. SERIALISE
# =====================================================================
workflow = {
    "name": "Quadrum - Project Expense Processing",
    "nodes": nodes,
    "connections": conn,
    "active": False,
    "pinData": {},
    "settings": {"executionOrder": "v1", "saveManualExecutions": True,
                 "callerPolicy": "workflowsFromSameOwner"},
    "versionId": uid(),
    "meta": {"instanceId": "quadrum-expense-workflow"},
    "tags": []
}

names = [n["name"] for n in nodes]
assert len(names) == len(set(names)), "duplicate node names: " + str(
    [x for x in names if names.count(x) > 1])
for src, spec in conn.items():
    assert src in names, "connection from unknown node: " + src
    for branch in spec["main"]:
        for c in branch:
            assert c["node"] in names, "connection to unknown node: " + c["node"]

out = "/home/user/Quadrum/quadrum-expense-workflow.json"
with open(out, "w") as f:
    json.dump(workflow, f, indent=2)

logic_nodes = [n for n in nodes if n["type"] != "n8n-nodes-base.stickyNote"]
print("total nodes:", len(nodes), "(logic:", len(logic_nodes), ", sticky notes:",
      len(nodes) - len(logic_nodes), ")")
print("written to", out)

