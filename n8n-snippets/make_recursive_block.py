#!/usr/bin/env python3
"""Generate a paste-able n8n node group that replaces the fixed-depth discovery
ladder with an unlimited-depth tree walk."""
import json, uuid

FOLDER_MIME = "application/vnd.google-apps.folder"
MY_DRIVE = {"__rl": True, "mode": "list", "value": "My Drive", "cachedResultName": "My Drive"}

def uid():
    return str(uuid.uuid4())

nodes = []
conn = {}

def link(src, dst):
    conn.setdefault(src, {"main": []})
    while len(conn[src]["main"]) < 1:
        conn[src]["main"].append([])
    conn[src]["main"][0].append({"node": dst, "type": "main", "index": 0})

# 1. List every folder in the drive (folders are far fewer than files)
nodes.append({
    "parameters": {
        "resource": "fileFolder", "operation": "search", "searchMethod": "query",
        "queryString": "=mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        "returnAll": True,
        "filter": {"driveId": dict(MY_DRIVE)},
        "options": {"fields": ["id", "name", "mimeType", "parents"]},
    },
    "id": uid(), "name": "List All Folders In Drive",
    "type": "n8n-nodes-base.googleDrive", "typeVersion": 3, "position": [0, -950],
})

# 2. Walk down from the project folder to any depth
nodes.append({
    "parameters": {
        "mode": "runOnceForAllItems", "language": "javaScript",
        "jsCode": r"""const ctx = $('Folder Context').first().json;
const skip = new Set([ctx.processedFolderId, ctx.uncompletedFolderId, ctx.processedInvoicesFolderId]);
const all = $input.all().map(i => i.json).filter(f => f && f.id);

// Fail loudly rather than silently missing invoices.
if (!all.some(f => Array.isArray(f.parents) && f.parents.length)) {
  throw new Error('Drive did not return "parents". Open "List All Folders In Drive" -> Options -> Fields and make sure "parents" is included.');
}

// parent id -> child folders
const childrenOf = new Map();
for (const f of all) {
  for (const p of (f.parents || [])) {
    if (!childrenOf.has(p)) childrenOf.set(p, []);
    childrenOf.get(p).push(f);
  }
}

// Breadth-first walk from the project folder - no depth limit.
const out = [{ json: { id: ctx.projectFolderId, name: ctx.projectName, depth: 0 } }];
const queue = [{ id: ctx.projectFolderId, depth: 0 }];
const seen = new Set([ctx.projectFolderId]);
while (queue.length) {
  const cur = queue.shift();
  for (const child of (childrenOf.get(cur.id) || [])) {
    if (seen.has(child.id) || skip.has(child.id)) continue;
    seen.add(child.id);
    out.push({ json: { id: child.id, name: child.name, depth: cur.depth + 1 } });
    queue.push({ id: child.id, depth: cur.depth + 1 });
  }
}
return out;""",
    },
    "id": uid(), "name": "Find All Subfolders (Any Depth)",
    "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [260, -950],
})

# 3. List the contents of every folder found (runs once per folder)
nodes.append({
    "parameters": {
        "resource": "fileFolder", "operation": "search", "searchMethod": "query",
        "queryString": "={{ \"'\" + $json.id + \"' in parents and trashed = false\" }}",
        "returnAll": True,
        "filter": {"driveId": dict(MY_DRIVE)},
        "options": {"fields": ["id", "name", "mimeType", "parents"]},
    },
    "id": uid(), "name": "List Files In Each Folder",
    "type": "n8n-nodes-base.googleDrive", "typeVersion": 3, "position": [520, -950],
})

# 4. Keep files, drop folders
nodes.append({
    "parameters": {
        "conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"},
            "conditions": [{
                "id": uid(), "leftValue": "={{ $json.mimeType }}",
                "rightValue": FOLDER_MIME,
                "operator": {"type": "string", "operation": "notEquals"},
            }],
            "combinator": "and",
        },
        "options": {},
    },
    "id": uid(), "name": "Files Only (All Levels)",
    "type": "n8n-nodes-base.filter", "typeVersion": 2.2, "position": [780, -950],
})

link("List All Folders In Drive", "Find All Subfolders (Any Depth)")
link("Find All Subfolders (Any Depth)", "List Files In Each Folder")
link("List Files In Each Folder", "Files Only (All Levels)")

snippet = {"nodes": nodes, "connections": conn}
out_path = "/tmp/claude-0/-home-user-Quadrum/bfe813d0-f3a6-5305-b601-df62f488d6d1/scratchpad/n8n/recursive_block.json"
with open(out_path, "w") as f:
    json.dump(snippet, f, indent=2)
print(json.dumps(snippet, indent=2))
