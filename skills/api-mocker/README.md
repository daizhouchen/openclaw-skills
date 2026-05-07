> 📦 Part of [**openclaw-skills**](../../) monorepo
> Status: **experimental archive** · originally pushed 2026-03-31 ~ 2026-04-01
> One-liner: OpenAPI → 可运行的 Express mock 服务（带 smart fake data / CRUD）

---

# api-mocker

> Drop in a spec, spin up a mock -- your backend-less frontend workflow starts here.

An [OpenClaw](https://openclawskill.ai) skill that generates a fully functional Express.js mock API server from OpenAPI/Swagger specifications or verbal descriptions. It parses your API definition, produces realistic fake data with referential integrity, and outputs a ready-to-run server with full CRUD, pagination, and CORS -- all in seconds.

## Demo

Given the included sample e-commerce spec, the skill produces a running server you can immediately query:

```bash
# List users with pagination
curl http://localhost:3456/api/users?page=1&limit=2
```

```json
{
  "data": [
    {
      "id": 1,
      "name": "Julia Martin",
      "email": "linda.smith@demo.net",
      "phone": "+1-868-592-2895",
      "address": "5765 Park Blvd",
      "city": "Denver",
      "created_at": "2024-09-11T06:53:00Z"
    },
    {
      "id": 2,
      "name": "Wendy Thomas",
      "email": "george.davis@mock.io",
      "phone": "+1-443-271-8190",
      "address": "1023 Elm St",
      "city": "Austin",
      "created_at": "2024-04-18T14:22:00Z"
    }
  ],
  "pagination": { "page": 1, "limit": 2, "total": 12, "totalPages": 6 }
}
```

```bash
# Create a product
curl -X POST http://localhost:3456/api/products \
  -H "Content-Type: application/json" \
  -d '{"title": "Wireless Charger", "price": 29.99, "category": "Electronics"}'
```

```json
{ "id": 16, "title": "Wireless Charger", "price": 29.99, "category": "Electronics" }
```

```bash
# Get a single order
curl http://localhost:3456/api/orders/3
```

```json
{
  "id": 3,
  "user_id": 5,
  "product_id": 8,
  "quantity": 42,
  "total_price": 387.14,
  "status": "shipped",
  "shipping_address": "2910 Cedar Ln",
  "created_at": "2024-07-02T19:45:00Z"
}
```

## Features

- **OpenAPI 3.0 Parsing** -- Full `$ref` resolution, `allOf` merging, `oneOf`/`anyOf` handling (picks first variant), path and operation-level parameters, request body extraction
- **Smart Fake Data** -- Field-name inference maps names like `email`, `price`, `city` to realistic generated values (see Fake Data Intelligence below)
- **Referential Integrity** -- Foreign key fields (`user_id`, `product_id`) reference real IDs from related resources via topological sort of generation order
- **Full CRUD** -- Every resource gets GET (list + detail), POST (create), PUT/PATCH (update), and DELETE endpoints with an in-memory store
- **Pagination** -- All list endpoints support `?page=1&limit=10` with total count and total pages
- **CORS Enabled** -- All origins, methods, and common headers allowed out of the box
- **Configurable Latency** -- Simulate slow networks with the `DELAY_MS` environment variable
- **Health Check** -- Built-in `/health` endpoint returns server status and timestamp
- **API Index** -- Root `/` endpoint lists all available routes with methods and summaries
- **Deterministic Seed** -- Fake data uses seed `42` by default for reproducible output

## Installation

```bash
npx @anthropic-ai/claw@latest skill add daizhouchen/api-mocker
```

## Quick Start

```bash
# 1. Parse an OpenAPI spec into standardized route descriptions
python3 scripts/parse_openapi.py assets/sample-ecommerce.yaml -o /tmp/api-mocker/routes.json

# 2. Generate realistic fake data for every resource
python3 scripts/fake_data.py /tmp/api-mocker/routes.json -o /tmp/api-mocker/data

# 3. Scaffold the Express.js mock server
node scripts/generate_server.js /tmp/api-mocker/routes.json /tmp/api-mocker/data -o ./mock-server

# 4. Install dependencies and start
cd mock-server && npm install && node server.js
# => Mock server running at http://localhost:3456
```

When used as an OpenClaw skill, OpenClaw handles all four steps automatically -- just describe your API or point to a spec file.

## How It Works

The skill runs a three-stage pipeline, each handled by a dedicated script:

| Stage | Script | Input | Output |
|-------|--------|-------|--------|
| **Parse** | `parse_openapi.py` | OpenAPI YAML/JSON spec | `routes.json` -- standardized route descriptors with resolved `$ref`, merged `allOf`, extracted parameters, request bodies, and response schemas |
| **Data** | `fake_data.py` | `routes.json` | Per-resource JSON files (`users.json`, `products.json`, etc.) with 8-15 items each, referentially consistent foreign keys, and field-name-inferred values |
| **Server** | `generate_server.js` | `routes.json` + data directory | Complete Express.js project: `server.js`, per-resource route modules, data files, and `package.json` |

**Parse stage details:** Resolves `$ref` pointers recursively, merges `allOf` schemas by combining properties, handles `oneOf`/`anyOf` by selecting the first variant. Supports path-level and operation-level parameters. Extracts request bodies from `application/json` content types.

**Data stage details:** Uses topological sorting to determine generation order so that referenced resources (e.g., `users`) are created before dependent ones (e.g., `orders`). Foreign key fields like `user_id` are populated with IDs that actually exist in the referenced resource.

**Server stage details:** Groups routes by resource, generates an Express router module for each, wires them into a main `server.js` with CORS middleware, optional delay middleware, a health check, a root API index, and a 404 handler.

## API Endpoints

For the sample e-commerce spec, the generated server exposes:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/users` | List users (paginated) |
| `GET` | `/api/users/:id` | Get user by ID |
| `POST` | `/api/users` | Create a user |
| `PUT` | `/api/users/:id` | Update a user |
| `DELETE` | `/api/users/:id` | Delete a user |
| `GET` | `/api/products` | List products (paginated) |
| `GET` | `/api/products/:id` | Get product by ID |
| `POST` | `/api/products` | Create a product |
| `PUT` | `/api/products/:id` | Update a product |
| `DELETE` | `/api/products/:id` | Delete a product |
| `GET` | `/api/orders` | List orders (paginated) |
| `GET` | `/api/orders/:id` | Get order by ID |
| `POST` | `/api/orders` | Create an order |
| `PUT` | `/api/orders/:id` | Update an order |
| `DELETE` | `/api/orders/:id` | Delete an order |
| `GET` | `/health` | Health check |
| `GET` | `/` | API index (lists all endpoints) |

## Fake Data Intelligence

The data generator infers realistic values from field names -- no configuration needed:

| Field Name Pattern | Generated Value | Example |
|--------------------|----------------|---------|
| `name`, `username`, `full_name` | Person name | `"Alice Johnson"` |
| `first_name`, `fname` | First name | `"Charlie"` |
| `last_name`, `surname` | Last name | `"Garcia"` |
| `email` (or format: email) | Email address | `"bob.smith@demo.net"` |
| `phone`, `tel` | Phone number | `"+1-555-234-6789"` |
| `address`, `street` | Street address | `"4521 Oak Ave"` |
| `city` | City name | `"Seattle"` |
| `country` | Country code | `"US"` |
| `zip`, `postal` | ZIP code | `"90210"` |
| `state`, `province` | State code | `"CA"` |
| `title`, `product_name` | Product title | `"Premium Laptop"` |
| `description`, `body`, `content` | Description text | `"High-quality product..."` |
| `price`, `amount`, `cost`, `total` | Dollar amount (9.99-999.99) | `149.95` |
| `quantity`, `stock`, `count` | Integer (1-100) | `42` |
| `rating`, `score` | Float (1.0-5.0) | `4.2` |
| `age` | Integer (18-80) | `34` |
| `status` | Status string | `"shipped"` |
| `category`, `type` | Category string | `"Electronics"` |
| `image`, `avatar`, `photo` | Picsum URL | `"https://picsum.photos/400/300?random=42"` |
| `url`, `link`, `href` | Example URL | `"https://example.com/page/123"` |
| `password`, `token`, `secret` | Random alphanumeric (32 chars) | `"aB3x..."` |
| `*_at`, `date`, `time` (or date-time format) | ISO 8601 timestamp | `"2024-06-15T08:30:00Z"` |
| `color`, `colour` | Color name | `"Silver"` |
| `tag` | Tag string | `"featured"` |
| `*_id` (foreign key) | Valid ID from referenced resource | `5` |
| Enum fields | Random enum value | `"pending"` |

## Trigger Phrases

The skill activates when the user mentions any of the following:

**English:** `mock api`, `mock server`, `fake api`, `swagger mock`

**Chinese:** `假接口`, `前端联调`, `模拟后端`, `后端还没好我需要先开发前端`

## Generated Server Structure

```
mock-server/
├── server.js            # Express entry point with CORS, delay, health check
├── package.json         # express ^4.21.0 dependency
├── routes/
│   ├── users.js         # CRUD router for users
│   ├── products.js      # CRUD router for products
│   └── orders.js        # CRUD router for orders
└── data/
    ├── users.json       # Generated user records
    ├── products.json    # Generated product records
    └── orders.json      # Generated order records
```

## Project Structure

```
api-mocker/
├── SKILL.md                      # Skill definition and OpenClaw workflow
├── README.md
├── scripts/
│   ├── parse_openapi.py          # OpenAPI 3.0 parser ($ref, allOf, oneOf)
│   ├── fake_data.py              # Field-aware fake data generator
│   └── generate_server.js        # Express.js project scaffolder
└── assets/
    └── sample-ecommerce.yaml     # Sample OpenAPI spec (users, products, orders)
```

## Configuration

| Option | Mechanism | Default | Description |
|--------|-----------|---------|-------------|
| Port | `PORT` env var | `3456` | Server listening port |
| Latency | `DELAY_MS` env var | `0` | Artificial response delay in milliseconds |
| Item count | `-n` flag on `fake_data.py` | Random 8-15 | Number of items generated per resource |
| Output dir | `-o` flag on `generate_server.js` | `./mock-server` | Where the server project is written |
| Data seed | Hardcoded in `fake_data.py` | `42` | RNG seed for reproducible data |

## Requirements

- **Python 3.8+** -- runs `parse_openapi.py` and `fake_data.py`
- **PyYAML** (`pip install pyyaml`) -- required only for YAML spec files; JSON specs work without it
- **Node.js 16+** -- runs `generate_server.js` and the generated mock server
- **npm** -- installs Express in the generated server

## Limitations

- **In-memory data store** -- all mutations (POST, PUT, DELETE) are lost on server restart; this is by design for mock usage
- **No authentication** -- the generated server has no auth middleware
- **Simplified schema merging** -- `oneOf`/`anyOf` picks the first variant; deeply nested compositions may lose information
- **No file upload support** -- only `application/json` request bodies are handled
- **Single response type** -- only the first 2xx response schema is used per operation

## Contributing

Contributions are welcome. Fork the repo, make your changes, and open a pull request. Please keep scripts self-contained with no heavy dependencies.

## License

MIT
