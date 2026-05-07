#!/usr/bin/env python3
"""
fake_data.py - Generate smart fake data based on route descriptions.

Usage:
    python3 fake_data.py <routes.json> [-o output_dir] [-n count]

Features:
- Field name inference for realistic values
- Referential consistency across resources
- Pagination-ready list sizes (5-20 items)
"""

import argparse
import json
import hashlib
import math
import os
import random
import string
import sys
from datetime import datetime, timedelta


# --- Fake data pools ---

FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George", "Hannah",
    "Ivan", "Julia", "Kevin", "Linda", "Michael", "Nancy", "Oscar", "Patricia",
    "Quincy", "Rachel", "Steven", "Tina", "Uma", "Victor", "Wendy", "Xavier",
    "Yvonne", "Zachary",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
]

PRODUCT_ADJECTIVES = [
    "Premium", "Deluxe", "Professional", "Essential", "Classic", "Modern",
    "Ultra", "Slim", "Advanced", "Smart", "Eco", "Compact",
]

PRODUCT_NOUNS = [
    "Laptop", "Headphones", "Keyboard", "Mouse", "Monitor", "Tablet",
    "Camera", "Speaker", "Charger", "Cable", "Stand", "Backpack",
    "Watch", "Phone Case", "Stylus", "Hub", "Webcam", "Microphone",
]

PRODUCT_DESCRIPTIONS = [
    "High-quality product with excellent performance and durability.",
    "Best-in-class design with premium materials and craftsmanship.",
    "Affordable yet reliable option for everyday use.",
    "Top-rated by customers for its ease of use and value.",
    "Innovative design that combines style with functionality.",
]

STREET_NAMES = [
    "Main St", "Oak Ave", "Maple Dr", "Cedar Ln", "Pine Rd",
    "Elm St", "Washington Ave", "Park Blvd", "Lake Dr", "Hill Rd",
]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "San Francisco", "Seattle", "Denver", "Boston", "Austin",
]

STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]
CATEGORIES = ["Electronics", "Clothing", "Books", "Home", "Sports", "Food", "Toys"]
COLORS = ["Red", "Blue", "Green", "Black", "White", "Silver", "Gold"]

DOMAINS = ["example.com", "test.org", "mock.io", "demo.net", "sample.dev"]


class FakeDataGenerator:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.id_counters = {}
        self.resource_ids = {}  # resource_name -> list of generated IDs

    def next_id(self, resource):
        """Get the next sequential ID for a resource."""
        if resource not in self.id_counters:
            self.id_counters[resource] = 0
        self.id_counters[resource] += 1
        return self.id_counters[resource]

    def register_ids(self, resource, ids):
        """Register generated IDs for referential consistency."""
        self.resource_ids[resource] = ids

    def get_foreign_id(self, resource):
        """Get a random existing ID from another resource."""
        if resource in self.resource_ids and self.resource_ids[resource]:
            return self.rng.choice(self.resource_ids[resource])
        return self.rng.randint(1, 10)

    def fake_value(self, field_name, field_type="string", field_format=None, field_enum=None):
        """Generate a fake value based on field name and type inference."""
        name = field_name.lower().replace("_", "").replace("-", "")

        if field_enum:
            return self.rng.choice(field_enum)

        # ID fields
        if name == "id":
            return None  # handled separately
        if name.endswith("id") and len(name) > 2:
            # Foreign key - extract resource name
            ref_resource = name[:-2]
            # Try common pluralizations
            for suffix in ["s", "es", ""]:
                key = ref_resource + suffix
                if key in self.resource_ids:
                    return self.get_foreign_id(key)
            return self.rng.randint(1, 20)

        # String types by field name
        if field_type == "string" or field_type is None:
            if "email" in name or field_format == "email":
                first = self.rng.choice(FIRST_NAMES).lower()
                last = self.rng.choice(LAST_NAMES).lower()
                domain = self.rng.choice(DOMAINS)
                return f"{first}.{last}@{domain}"

            if "phone" in name or "tel" in name:
                return f"+1-{self.rng.randint(200,999)}-{self.rng.randint(100,999)}-{self.rng.randint(1000,9999)}"

            if name in ("name", "fullname", "full_name", "username", "displayname"):
                return f"{self.rng.choice(FIRST_NAMES)} {self.rng.choice(LAST_NAMES)}"

            if name in ("firstname", "first_name", "fname"):
                return self.rng.choice(FIRST_NAMES)

            if name in ("lastname", "last_name", "lname", "surname"):
                return self.rng.choice(LAST_NAMES)

            if "title" in name or name == "productname" or name == "product_name":
                return f"{self.rng.choice(PRODUCT_ADJECTIVES)} {self.rng.choice(PRODUCT_NOUNS)}"

            if "description" in name or "desc" in name or "body" in name or "content" in name:
                return self.rng.choice(PRODUCT_DESCRIPTIONS)

            if "address" in name or "street" in name:
                return f"{self.rng.randint(100,9999)} {self.rng.choice(STREET_NAMES)}"

            if "city" in name:
                return self.rng.choice(CITIES)

            if "country" in name:
                return self.rng.choice(["US", "UK", "CA", "AU", "DE", "FR", "JP"])

            if "zip" in name or "postal" in name:
                return f"{self.rng.randint(10000, 99999)}"

            if "state" in name or "province" in name:
                return self.rng.choice(["CA", "NY", "TX", "WA", "FL", "IL", "CO", "MA"])

            if "status" in name:
                return self.rng.choice(STATUSES)

            if "category" in name or "type" in name:
                return self.rng.choice(CATEGORIES)

            if "color" in name or "colour" in name:
                return self.rng.choice(COLORS)

            if "image" in name or "avatar" in name or "photo" in name or "picture" in name:
                w, h = self.rng.choice([(200, 200), (400, 300), (800, 600)])
                return f"https://picsum.photos/{w}/{h}?random={self.rng.randint(1,1000)}"

            if "url" in name or "link" in name or "href" in name:
                return f"https://example.com/{self.rng.choice(['page','item','resource'])}/{self.rng.randint(1,1000)}"

            if "password" in name or "token" in name or "secret" in name:
                return "".join(self.rng.choices(string.ascii_letters + string.digits, k=32))

            if "date" in name or "time" in name or field_format in ("date", "date-time"):
                base = datetime(2024, 1, 1)
                offset = timedelta(days=self.rng.randint(0, 365), hours=self.rng.randint(0, 23), minutes=self.rng.randint(0, 59))
                dt = base + offset
                if field_format == "date":
                    return dt.strftime("%Y-%m-%d")
                return dt.isoformat() + "Z"

            if "tag" in name:
                return self.rng.choice(["sale", "new", "featured", "popular", "limited"])

            # Default string
            return f"{field_name}_{self.rng.randint(1000, 9999)}"

        # Numeric types
        if field_type in ("integer", "number"):
            if "price" in name or "amount" in name or "cost" in name or "total" in name:
                return round(self.rng.uniform(9.99, 999.99), 2)

            if "quantity" in name or "qty" in name or "count" in name or "stock" in name:
                return self.rng.randint(1, 100)

            if "rating" in name or "score" in name:
                return round(self.rng.uniform(1.0, 5.0), 1)

            if "age" in name:
                return self.rng.randint(18, 80)

            if "weight" in name:
                return round(self.rng.uniform(0.1, 50.0), 2)

            if field_type == "integer":
                return self.rng.randint(1, 1000)
            return round(self.rng.uniform(0.01, 10000.0), 2)

        if field_type == "boolean":
            return self.rng.choice([True, False])

        if field_type == "array":
            return []

        return f"{field_name}_value"

    def generate_object(self, properties, resource_name, item_id):
        """Generate a single object from a properties schema."""
        obj = {}
        for prop_name, prop_schema in properties.items():
            if prop_name == "id":
                obj["id"] = item_id
                continue

            prop_type = prop_schema.get("type", "string")
            prop_format = prop_schema.get("format")
            prop_enum = prop_schema.get("enum")

            if prop_type == "object" and "properties" in prop_schema:
                obj[prop_name] = self.generate_object(prop_schema["properties"], resource_name, item_id)
            elif prop_type == "array" and "items" in prop_schema:
                items_schema = prop_schema["items"]
                count = self.rng.randint(1, 3)
                if items_schema.get("type") == "object" and "properties" in items_schema:
                    obj[prop_name] = [
                        self.generate_object(items_schema["properties"], resource_name, item_id)
                        for _ in range(count)
                    ]
                else:
                    obj[prop_name] = [
                        self.fake_value(prop_name, items_schema.get("type", "string"))
                        for _ in range(count)
                    ]
            else:
                obj[prop_name] = self.fake_value(prop_name, prop_type, prop_format, prop_enum)

        return obj

    def extract_resource_name(self, path):
        """Extract the resource name from a path like /api/users/{id}."""
        parts = [p for p in path.split("/") if p and not p.startswith("{")]
        if parts:
            # Return the last non-parameter segment
            return parts[-1].lower()
        return "items"

    def generate_data(self, routes_data, count_range=(8, 15)):
        """Generate fake data for all resources found in routes."""
        resources = {}

        # First pass: identify resources from GET list endpoints
        for route in routes_data.get("routes", []):
            path = route["path"]
            method = route["method"]

            # Look for list endpoints (GET without path params at end)
            if method == "GET" and not path.rstrip("/").endswith("}"):
                resource_name = self.extract_resource_name(path)
                schema = route.get("response", {}).get("schema", {})

                # Get the item schema
                item_schema = None
                if schema.get("type") == "array" and "items" in schema:
                    item_schema = schema["items"]
                elif schema.get("type") == "object" and "properties" in schema:
                    # Could be paginated response
                    props = schema["properties"]
                    for key in ["data", "items", "results", "records", resource_name]:
                        if key in props and props[key].get("type") == "array":
                            item_schema = props[key].get("items", {})
                            break
                    if not item_schema:
                        item_schema = schema

                if item_schema and item_schema.get("properties"):
                    resources[resource_name] = item_schema

        # If no list endpoints found, try POST endpoints for schemas
        if not resources:
            for route in routes_data.get("routes", []):
                if route["method"] == "POST":
                    resource_name = self.extract_resource_name(route["path"])
                    body = route.get("requestBody", {})
                    if body.get("properties"):
                        resources[resource_name] = body

        # Determine generation order: resources without foreign keys first
        ordered = self._order_resources(resources)

        all_data = {}

        for resource_name in ordered:
            schema = resources[resource_name]
            count = self.rng.randint(*count_range)
            items = []

            for i in range(count):
                item_id = self.next_id(resource_name)
                obj = self.generate_object(schema.get("properties", {}), resource_name, item_id)
                items.append(obj)

            all_data[resource_name] = items
            self.register_ids(resource_name, [item["id"] for item in items if "id" in item])

        return all_data

    def _order_resources(self, resources):
        """Order resources so that referenced resources are generated first."""
        # Simple heuristic: resources whose names appear as foreign keys in others go first
        names = list(resources.keys())
        deps = {name: [] for name in names}

        for name, schema in resources.items():
            for prop_name in schema.get("properties", {}):
                pn = prop_name.lower().replace("_", "")
                if pn.endswith("id") and len(pn) > 2:
                    ref = pn[:-2]
                    for other in names:
                        if other != name and (other.startswith(ref) or ref.startswith(other.rstrip("s"))):
                            deps[name].append(other)

        # Topological sort (simple)
        ordered = []
        visited = set()

        def visit(n):
            if n in visited:
                return
            visited.add(n)
            for dep in deps.get(n, []):
                visit(dep)
            ordered.append(n)

        for n in names:
            visit(n)

        return ordered


def main():
    parser = argparse.ArgumentParser(description="Generate fake data from route descriptions")
    parser.add_argument("routes_file", help="Path to routes.json")
    parser.add_argument("-o", "--output", default="./data", help="Output directory for data files")
    parser.add_argument("-n", "--count", default=None, type=int, help="Number of items per resource (default: random 8-15)")
    args = parser.parse_args()

    if not os.path.exists(args.routes_file):
        print(f"ERROR: File not found: {args.routes_file}", file=sys.stderr)
        sys.exit(1)

    with open(args.routes_file, "r", encoding="utf-8") as f:
        routes_data = json.load(f)

    gen = FakeDataGenerator(seed=42)

    count_range = (args.count, args.count) if args.count else (8, 15)
    all_data = gen.generate_data(routes_data, count_range)

    os.makedirs(args.output, exist_ok=True)

    for resource_name, items in all_data.items():
        filepath = os.path.join(args.output, f"{resource_name}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        print(f"Generated {len(items)} {resource_name} -> {filepath}")

    print(f"\nDone. {len(all_data)} resource(s) written to {args.output}/")


if __name__ == "__main__":
    main()
