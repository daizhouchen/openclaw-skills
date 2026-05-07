#!/usr/bin/env node
/**
 * generate_server.js - Generate a complete Express.js mock server from route descriptions.
 *
 * Usage:
 *   node generate_server.js <routes.json> <data_dir> [-o output_dir]
 *
 * Generates:
 *   - server.js (main entry point)
 *   - routes/ (one file per resource)
 *   - data/ (copied fake data JSONs)
 *   - package.json
 */

const fs = require("fs");
const path = require("path");

// --- Parse arguments ---
const args = process.argv.slice(2);
let routesFile = null;
let dataDir = null;
let outputDir = "./mock-server";

for (let i = 0; i < args.length; i++) {
  if (args[i] === "-o" && args[i + 1]) {
    outputDir = args[++i];
  } else if (!routesFile) {
    routesFile = args[i];
  } else if (!dataDir) {
    dataDir = args[i];
  }
}

if (!routesFile || !dataDir) {
  console.error(
    "Usage: node generate_server.js <routes.json> <data_dir> [-o output_dir]"
  );
  process.exit(1);
}

// --- Load inputs ---
const routesData = JSON.parse(fs.readFileSync(routesFile, "utf-8"));
const routes = routesData.routes || [];
const info = routesData.info || { title: "Mock API", version: "1.0.0" };

// --- Identify resources ---
// Group routes by resource name
function extractResourceName(routePath) {
  const parts = routePath
    .split("/")
    .filter((p) => p && !p.startsWith("{") && !p.startsWith(":"));
  return parts.length > 0 ? parts[parts.length - 1].toLowerCase() : "items";
}

const resourceRoutes = {};
for (const route of routes) {
  const resource = extractResourceName(route.path);
  if (!resourceRoutes[resource]) {
    resourceRoutes[resource] = [];
  }
  resourceRoutes[resource].push(route);
}

// --- Create output directories ---
fs.mkdirSync(path.join(outputDir, "routes"), { recursive: true });
fs.mkdirSync(path.join(outputDir, "data"), { recursive: true });

// --- Copy data files ---
if (fs.existsSync(dataDir)) {
  const dataFiles = fs
    .readdirSync(dataDir)
    .filter((f) => f.endsWith(".json"));
  for (const file of dataFiles) {
    fs.copyFileSync(
      path.join(dataDir, file),
      path.join(outputDir, "data", file)
    );
  }
}

// --- Generate package.json ---
const packageJson = {
  name: info.title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, ""),
  version: info.version || "1.0.0",
  description: `Mock server for ${info.title}`,
  main: "server.js",
  scripts: {
    start: "node server.js",
  },
  dependencies: {
    express: "^4.21.0",
  },
};

fs.writeFileSync(
  path.join(outputDir, "package.json"),
  JSON.stringify(packageJson, null, 2)
);

// --- Generate route files ---
const resourceNames = Object.keys(resourceRoutes);

for (const resource of resourceNames) {
  const routeList = resourceRoutes[resource];
  const dataFile = `${resource}.json`;
  const hasData = fs.existsSync(path.join(outputDir, "data", dataFile));

  let code = `const express = require('express');\n`;
  code += `const router = express.Router();\n`;
  code += `const path = require('path');\n`;
  code += `const fs = require('fs');\n\n`;

  // Load data
  code += `// Load initial data\n`;
  code += `let items = [];\n`;
  code += `const dataPath = path.join(__dirname, '..', 'data', '${dataFile}');\n`;
  code += `if (fs.existsSync(dataPath)) {\n`;
  code += `  items = JSON.parse(fs.readFileSync(dataPath, 'utf-8'));\n`;
  code += `}\n\n`;

  code += `// Helper: find next ID\n`;
  code += `function nextId() {\n`;
  code += `  if (items.length === 0) return 1;\n`;
  code += `  return Math.max(...items.map(i => i.id || 0)) + 1;\n`;
  code += `}\n\n`;

  // Determine the base path for this resource
  // Find the common prefix among all routes for this resource
  const basePaths = routeList.map((r) => r.path);
  const listPath = basePaths.find(
    (p) => !p.endsWith("}") && p.includes(resource)
  );

  // Determine Express-style paths
  const expressBasePath = listPath
    ? listPath.replace(/\{([^}]+)\}/g, ":$1")
    : `/${resource}`;
  const expressDetailPath = expressBasePath.replace(/\/$/, "") + "/:id";

  // Check which methods exist
  const methods = new Set(routeList.map((r) => r.method));

  // GET list
  if (methods.has("GET")) {
    code += `// GET list - with pagination\n`;
    code += `router.get('/', (req, res) => {\n`;
    code += `  const page = parseInt(req.query.page) || 1;\n`;
    code += `  const limit = parseInt(req.query.limit) || 10;\n`;
    code += `  const start = (page - 1) * limit;\n`;
    code += `  const end = start + limit;\n`;
    code += `  const paged = items.slice(start, end);\n`;
    code += `  res.json({\n`;
    code += `    data: paged,\n`;
    code += `    pagination: {\n`;
    code += `      page,\n`;
    code += `      limit,\n`;
    code += `      total: items.length,\n`;
    code += `      totalPages: Math.ceil(items.length / limit)\n`;
    code += `    }\n`;
    code += `  });\n`;
    code += `});\n\n`;

    code += `// GET by ID\n`;
    code += `router.get('/:id', (req, res) => {\n`;
    code += `  const id = parseInt(req.params.id) || req.params.id;\n`;
    code += `  const item = items.find(i => i.id === id || i.id === parseInt(req.params.id));\n`;
    code += `  if (!item) return res.status(404).json({ error: 'Not found' });\n`;
    code += `  res.json(item);\n`;
    code += `});\n\n`;
  }

  // POST create
  if (methods.has("POST")) {
    code += `// POST create\n`;
    code += `router.post('/', (req, res) => {\n`;
    code += `  const newItem = { id: nextId(), ...req.body };\n`;
    code += `  items.push(newItem);\n`;
    code += `  res.status(201).json(newItem);\n`;
    code += `});\n\n`;
  }

  // PUT update
  if (methods.has("PUT") || methods.has("PATCH")) {
    code += `// PUT/PATCH update\n`;
    code += `router.put('/:id', (req, res) => {\n`;
    code += `  const id = parseInt(req.params.id) || req.params.id;\n`;
    code += `  const index = items.findIndex(i => i.id === id || i.id === parseInt(req.params.id));\n`;
    code += `  if (index === -1) return res.status(404).json({ error: 'Not found' });\n`;
    code += `  items[index] = { ...items[index], ...req.body };\n`;
    code += `  res.json(items[index]);\n`;
    code += `});\n\n`;

    code += `router.patch('/:id', (req, res) => {\n`;
    code += `  const id = parseInt(req.params.id) || req.params.id;\n`;
    code += `  const index = items.findIndex(i => i.id === id || i.id === parseInt(req.params.id));\n`;
    code += `  if (index === -1) return res.status(404).json({ error: 'Not found' });\n`;
    code += `  items[index] = { ...items[index], ...req.body };\n`;
    code += `  res.json(items[index]);\n`;
    code += `});\n\n`;
  }

  // DELETE
  if (methods.has("DELETE")) {
    code += `// DELETE\n`;
    code += `router.delete('/:id', (req, res) => {\n`;
    code += `  const id = parseInt(req.params.id) || req.params.id;\n`;
    code += `  const index = items.findIndex(i => i.id === id || i.id === parseInt(req.params.id));\n`;
    code += `  if (index === -1) return res.status(404).json({ error: 'Not found' });\n`;
    code += `  const deleted = items.splice(index, 1)[0];\n`;
    code += `  res.json({ message: 'Deleted', item: deleted });\n`;
    code += `});\n\n`;
  }

  code += `module.exports = router;\n`;

  fs.writeFileSync(path.join(outputDir, "routes", `${resource}.js`), code);
}

// --- Generate server.js ---
let serverCode = `const express = require('express');\n`;
serverCode += `const app = express();\n`;
serverCode += `const PORT = process.env.PORT || 3456;\n`;
serverCode += `const DELAY_MS = parseInt(process.env.DELAY_MS) || 0;\n\n`;

serverCode += `// Middleware\n`;
serverCode += `app.use(express.json());\n`;
serverCode += `app.use(express.urlencoded({ extended: true }));\n\n`;

serverCode += `// CORS\n`;
serverCode += `app.use((req, res, next) => {\n`;
serverCode += `  res.header('Access-Control-Allow-Origin', '*');\n`;
serverCode += `  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS');\n`;
serverCode += `  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');\n`;
serverCode += `  if (req.method === 'OPTIONS') return res.sendStatus(200);\n`;
serverCode += `  next();\n`;
serverCode += `});\n\n`;

serverCode += `// Configurable delay\n`;
serverCode += `if (DELAY_MS > 0) {\n`;
serverCode += `  app.use((req, res, next) => {\n`;
serverCode += `    setTimeout(next, DELAY_MS);\n`;
serverCode += `  });\n`;
serverCode += `}\n\n`;

serverCode += `// Routes\n`;
for (const resource of resourceNames) {
  // Find the base API path for this resource
  const routeList = resourceRoutes[resource];
  const listRoute = routeList.find(
    (r) => r.method === "GET" && !r.path.endsWith("}")
  );
  let mountPath;
  if (listRoute) {
    mountPath = listRoute.path.replace(/\{([^}]+)\}/g, ":$1");
  } else {
    // Use the path from any route, stripping trailing /{param}
    const anyPath = routeList[0].path;
    mountPath = anyPath
      .replace(/\/\{[^}]+\}$/, "")
      .replace(/\{([^}]+)\}/g, ":$1");
  }
  serverCode += `app.use('${mountPath}', require('./routes/${resource}'));\n`;
}

serverCode += `\n// Health check\n`;
serverCode += `app.get('/health', (req, res) => {\n`;
serverCode += `  res.json({ status: 'ok', timestamp: new Date().toISOString() });\n`;
serverCode += `});\n\n`;

serverCode += `// API index\n`;
serverCode += `app.get('/', (req, res) => {\n`;
serverCode += `  res.json({\n`;
serverCode += `    name: ${JSON.stringify(info.title)},\n`;
serverCode += `    version: ${JSON.stringify(info.version)},\n`;
serverCode += `    endpoints: [\n`;
for (const route of routes) {
  const expressPath = route.path.replace(/\{([^}]+)\}/g, ":$1");
  serverCode += `      { method: '${route.method}', path: '${expressPath}', summary: ${JSON.stringify(route.summary || "")} },\n`;
}
serverCode += `    ]\n`;
serverCode += `  });\n`;
serverCode += `});\n\n`;

serverCode += `// 404 handler\n`;
serverCode += `app.use((req, res) => {\n`;
serverCode += `  res.status(404).json({ error: 'Not found', path: req.path });\n`;
serverCode += `});\n\n`;

serverCode += `app.listen(PORT, '0.0.0.0', () => {\n`;
serverCode += `  console.log('Mock server running at http://localhost:' + PORT);\n`;
serverCode += `  console.log('Press Ctrl+C to stop.');\n`;
serverCode += `});\n`;

fs.writeFileSync(path.join(outputDir, "server.js"), serverCode);

// --- Summary ---
console.log(`\nMock server generated in: ${outputDir}`);
console.log(`  - server.js`);
console.log(`  - package.json`);
console.log(`  - routes/ (${resourceNames.length} resource(s): ${resourceNames.join(", ")})`);
console.log(`  - data/`);
console.log(`\nTo start:`);
console.log(`  cd ${outputDir}`);
console.log(`  npm install`);
console.log(`  node server.js`);
console.log(`\nServer will run on port 3456 (or set PORT env var)`);
