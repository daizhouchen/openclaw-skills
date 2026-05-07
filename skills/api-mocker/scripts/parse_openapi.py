#!/usr/bin/env python3
"""
parse_openapi.py - Parse OpenAPI 3.0 YAML/JSON specs into standardized route descriptions.

Usage:
    python3 parse_openapi.py <spec_file> [-o output.json]

Outputs a routes.json with all endpoints, methods, parameters, and response schemas.
"""

import argparse
import json
import os
import sys

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load_spec(filepath):
    """Load an OpenAPI spec from YAML or JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if filepath.endswith((".yaml", ".yml")):
        if not HAS_YAML:
            print("ERROR: PyYAML is required for YAML files. Install with: pip install pyyaml", file=sys.stderr)
            sys.exit(1)
        return yaml.safe_load(content)
    else:
        return json.loads(content)


def resolve_ref(spec, ref_path):
    """Resolve a $ref pointer like '#/components/schemas/User'."""
    if not ref_path.startswith("#/"):
        return {"type": "object", "properties": {}}

    parts = ref_path[2:].split("/")
    node = spec
    for part in parts:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return {"type": "object", "properties": {}}
    return node


def resolve_schema(spec, schema):
    """Recursively resolve all $ref references in a schema."""
    if schema is None:
        return {"type": "object", "properties": {}}

    if isinstance(schema, dict):
        if "$ref" in schema:
            resolved = resolve_ref(spec, schema["$ref"])
            return resolve_schema(spec, resolved)

        result = {}
        for key, value in schema.items():
            if key == "properties" and isinstance(value, dict):
                result[key] = {}
                for prop_name, prop_val in value.items():
                    result[key][prop_name] = resolve_schema(spec, prop_val)
            elif key == "items":
                result[key] = resolve_schema(spec, value)
            elif key == "allOf" and isinstance(value, list):
                # Merge allOf schemas
                merged = {"type": "object", "properties": {}}
                for sub in value:
                    resolved_sub = resolve_schema(spec, sub)
                    if "properties" in resolved_sub:
                        merged["properties"].update(resolved_sub["properties"])
                return merged
            elif key == "oneOf" or key == "anyOf":
                # Take the first option for simplicity
                if isinstance(value, list) and len(value) > 0:
                    return resolve_schema(spec, value[0])
            else:
                result[key] = value
        return result

    return schema


def extract_parameters(spec, params_list):
    """Extract parameters from an operation."""
    params = []
    if not params_list:
        return params

    for param in params_list:
        if "$ref" in param:
            param = resolve_ref(spec, param["$ref"])

        p = {
            "name": param.get("name", ""),
            "in": param.get("in", "query"),
            "required": param.get("required", False),
            "type": "string",
        }

        schema = param.get("schema", {})
        if schema:
            resolved = resolve_schema(spec, schema)
            p["type"] = resolved.get("type", "string")
            if "format" in resolved:
                p["format"] = resolved["format"]
            if "enum" in resolved:
                p["enum"] = resolved["enum"]

        params.append(p)

    return params


def extract_request_body(spec, request_body):
    """Extract request body schema."""
    if not request_body:
        return None

    if "$ref" in request_body:
        request_body = resolve_ref(spec, request_body["$ref"])

    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})

    if schema:
        return resolve_schema(spec, schema)
    return None


def extract_response(spec, responses):
    """Extract the primary success response schema."""
    if not responses:
        return {"status": 200, "schema": {"type": "object", "properties": {}}}

    # Look for 200, 201, or first 2xx response
    for status_code in ["200", "201", "202", "204"]:
        if status_code in responses:
            resp = responses[status_code]
            if "$ref" in resp:
                resp = resolve_ref(spec, resp["$ref"])

            content = resp.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})

            return {
                "status": int(status_code),
                "schema": resolve_schema(spec, schema) if schema else {"type": "object", "properties": {}},
            }

    # Default
    return {"status": 200, "schema": {"type": "object", "properties": {}}}


def parse_spec(spec):
    """Parse a full OpenAPI spec into standardized route descriptions."""
    info = spec.get("info", {})
    paths = spec.get("paths", {})

    routes = []

    for path, path_item in paths.items():
        # Collect path-level parameters
        path_params = path_item.get("parameters", [])

        for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
            if method not in path_item:
                continue

            operation = path_item[method]

            # Merge path-level and operation-level parameters
            op_params = operation.get("parameters", [])
            all_params = path_params + op_params

            route = {
                "path": path,
                "method": method.upper(),
                "summary": operation.get("summary", ""),
                "operationId": operation.get("operationId", ""),
                "tags": operation.get("tags", []),
                "parameters": extract_parameters(spec, all_params),
                "response": extract_response(spec, operation.get("responses", {})),
            }

            # Add request body for POST/PUT/PATCH
            if method in ("post", "put", "patch"):
                body = extract_request_body(spec, operation.get("requestBody"))
                if body:
                    route["requestBody"] = body

            routes.append(route)

    return {
        "info": {
            "title": info.get("title", "Mock API"),
            "version": info.get("version", "1.0.0"),
            "description": info.get("description", ""),
        },
        "routes": routes,
    }


def main():
    parser = argparse.ArgumentParser(description="Parse OpenAPI spec into route descriptions")
    parser.add_argument("spec_file", help="Path to OpenAPI YAML/JSON file")
    parser.add_argument("-o", "--output", default=None, help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    if not os.path.exists(args.spec_file):
        print(f"ERROR: File not found: {args.spec_file}", file=sys.stderr)
        sys.exit(1)

    spec = load_spec(args.spec_file)
    result = parse_spec(spec)

    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Wrote {len(result['routes'])} routes to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
