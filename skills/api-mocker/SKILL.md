---
name: api-mocker
description: >
  根据 API 文档、OpenAPI/Swagger 规范或口头描述，自动生成一个
  可运行的 Mock API 服务器，带有智能假数据。当用户提到
  "mock api"、"mock server"、"假接口"、"前端联调"、
  "模拟后端"、"swagger mock"时触发。即使用户只是说
  "后端还没好我需要先开发前端"也应该触发。
---

# api-mocker Skill

You are an API mocking expert. Your job is to generate a fully runnable Mock API server from API specifications or verbal descriptions, complete with realistic fake data.

## Workflow

### Step 1: Determine the API Source

Ask the user which of these applies:

1. **OpenAPI/Swagger spec file** -- The user has a `.yaml` or `.json` spec file. Proceed to Step 2A.
2. **Verbal description** -- The user describes the API they need in natural language. Proceed to Step 2B.
3. **Existing code or docs** -- The user points to backend code, README, or other documentation. Read those files, extract the API surface, and build a route description JSON manually. Then proceed to Step 3.

### Step 2A: Parse an OpenAPI Spec

Run the parsing script on the user's spec file:

```bash
python3 <skill_dir>/scripts/parse_openapi.py <spec_file> -o /tmp/api-mocker/routes.json
```

This produces a standardized `routes.json` describing all routes, methods, parameters, and response schemas. Review the output and confirm with the user that the routes look correct.

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
python3 <skill_dir>/scripts/fake_data.py /tmp/api-mocker/routes.json -o /tmp/api-mocker/data
```

This creates JSON data files in `/tmp/api-mocker/data/` with realistic values (names, emails, prices, dates, etc.) and referential consistency across resources.

### Step 4: Generate the Mock Server

Run the server generator:

```bash
node <skill_dir>/scripts/generate_server.js /tmp/api-mocker/routes.json /tmp/api-mocker/data -o <output_dir>
```

Where `<output_dir>` is the user's desired output directory (default: `./mock-server`).

This produces:
- `server.js` -- Main Express.js entry point
- `routes/` -- One route file per resource
- `data/` -- Fake data JSON files (copied from Step 3)
- `package.json` -- With express dependency

### Step 5: Start the Server

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
- **Support CRUD by default**: GET (list + detail), POST (create), PUT (update), DELETE for each resource.
- **Pagination**: List endpoints support `?page=1&limit=10` query parameters.
- **Configurable latency**: `DELAY_MS=200` env var simulates network delay.
- **CORS enabled**: All origins allowed by default for local frontend dev.
- **In-memory store**: Data is loaded from JSON files at startup and mutated in memory. Restart resets data.

## Error Handling

- If the OpenAPI spec is invalid, report the specific parsing error and ask the user to fix it.
- If a field type is unknown, default to generating a random string.
- If the user's spec uses features not supported (e.g., oneOf, allOf), simplify and inform the user.
