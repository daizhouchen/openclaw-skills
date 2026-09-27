---
name: api-mocker
description: 根据 OpenAPI/Swagger、接口文档或描述生成简单资源的本地 Express mock API。用于请求模拟后端或前端联调假接口。
---

# api-mocker Skill

Resolve `<skill_dir>` to the directory containing this `SKILL.md`. Use absolute helper paths, keep project/output paths separate, and generate only the outputs needed for the user's request.


You are an API mocking expert. Your job is to generate a fully runnable Mock API server from API specifications or verbal descriptions, complete with realistic fake data.

## Workflow

### Step 1: Determine the API Source

Use the source already provided. Ask only when the source is missing:

1. **OpenAPI/Swagger spec file** -- The user has a `.yaml` or `.json` spec file. Proceed to Step 2A.
2. **Verbal description** -- The user describes the API they need in natural language. Proceed to Step 2B.
3. **Existing code or docs** -- The user points to backend code, README, or other documentation. Read those files, extract the API surface, and build a route description JSON manually. Then proceed to Step 3.

### Step 2A: Parse an OpenAPI Spec

Run the parsing script on the user's spec file:

```bash
python3 "<skill_dir>/scripts/parse_openapi.py" <spec_file> -o /tmp/api-mocker/routes.json
```

This produces a standardized `routes.json` describing all routes, methods, parameters, and response schemas. Review parsed routes against the source; clarify only material ambiguities.

### Step 2B: Build Routes from Verbal Description

When the user describes their API verbally (e.g., "I need a user management API with CRUD plus an orders endpoint"):

1. Ask clarifying questions if needed (what resources? what fields? any relationships?).
2. Manually create a `routes.json` file at `/tmp/api-mocker/routes.json` following this schema:

```json
{
  "info": { "title": "...", "version": "1.0.0" },
  "routes": [
    {
      "path": "/api/users",
      "method": "GET",
      "summary": "List all users",
      "parameters": [],
      "response": {
        "status": 200,
        "schema": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": { "type": "integer" },
              "name": { "type": "string" },
              "email": { "type": "string", "format": "email" }
            }
          }
        }
      }
    }
  ]
}
```

### Step 3: Generate Fake Data

Run the fake data generator:

```bash
python3 "<skill_dir>/scripts/fake_data.py" /tmp/api-mocker/routes.json -o /tmp/api-mocker/data
```

This creates JSON data files in `/tmp/api-mocker/data/` with realistic values (names, emails, prices, dates, etc.) and referential consistency across resources.

### Step 4: Generate the Mock Server

Run the server generator:

```bash
node "<skill_dir>/scripts/generate_server.js" /tmp/api-mocker/routes.json /tmp/api-mocker/data -o <output_dir>
```

Where `<output_dir>` is the user's desired output directory (default: `./mock-server`).

This produces:
- `server.js` -- Main Express.js entry point
- `routes/` -- One route file per resource
- `data/` -- Fake data JSON files (copied from Step 3)
- `package.json` -- With express dependency

### Step 5: Start the Server

Run the server when local verification is part of the task; stop it after checks unless the user needs it running. The generated server currently binds all network interfaces, so keep it in an isolated development environment.

```bash
cd <output_dir>
npm install
node server.js
```

The server runs on port 3456 by default (configurable via `PORT` env var).

Tell the user:
- The server URL (e.g., `http://localhost:3456`)
- All available endpoints with methods
- How to customize: edit data files, change port, add delay with `DELAY_MS` env var
- CORS is enabled by default for frontend development

### Step 6: Verify

Curl a few key endpoints to verify the server works, then present the results to the user.

## Key Behaviors

- **Always generate realistic data**: Use field name inference (name -> person name, email -> valid email, price -> reasonable dollar amount, created_at -> recent ISO date).
- **Maintain referential integrity**: If orders reference user_id, those IDs must exist in the users data.
- **Simple resource model**: The generator uses in-memory list/detail routes and methods found in the specification. Review nested routes and custom operations before claiming endpoint parity.
- **Pagination**: List endpoints support `?page=1&limit=10` query parameters.
- **Configurable latency**: `DELAY_MS=200` env var simulates network delay.
- **CORS enabled**: All origins allowed by default for local frontend dev.
- **In-memory store**: Data is loaded from JSON files at startup and mutated in memory. Restart resets data.

## Error Handling

- If the OpenAPI spec is invalid, report the specific parsing error and ask the user to fix it.
- If a field type is unknown, default to generating a random string.
- If the user's spec uses features not supported (e.g., oneOf, allOf), simplify and inform the user.
