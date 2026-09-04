const ctx = $('Folder Context').first().json;
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
// Each folder carries its readable path so the reports can say where a file came from.
const rootPath = ctx.projectName;
const out = [{ json: { id: ctx.projectFolderId, name: ctx.projectName, depth: 0, path: rootPath } }];
const queue = [{ id: ctx.projectFolderId, depth: 0, path: rootPath }];
const seen = new Set([ctx.projectFolderId]);
while (queue.length) {
  const cur = queue.shift();
  for (const child of (childrenOf.get(cur.id) || [])) {
    if (seen.has(child.id) || skip.has(child.id)) continue;
    seen.add(child.id);
    const childPath = cur.path + ' / ' + child.name;
    out.push({ json: { id: child.id, name: child.name, depth: cur.depth + 1, path: childPath } });
    queue.push({ id: child.id, depth: cur.depth + 1, path: childPath });
  }
}
return out;
