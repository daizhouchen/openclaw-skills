# Commit Message Examples by Diff Type

This document provides example commit messages in all six styles for five common types of changes.

---

## 1. New Feature

**Scenario:** Added a new user registration endpoint with email verification.

**Diff summary:**
- `src/routes/register.ts` (new file, +87 lines)
- `src/services/email.ts` (new file, +45 lines)
- `src/models/user.ts` (modified, +12 lines)
- `tests/register.test.ts` (new file, +63 lines)

### conventional
```
feat(auth): add user registration with email verification

- Add POST /api/auth/register endpoint
- Implement email verification service with token generation
- Extend user model with emailVerified and verificationToken fields
- Add integration tests for registration flow
```

### emoji
```
✨ Add user registration with email verification
📧 Implement verification email service
✅ Add registration flow integration tests
```

### poetic
```
A door now opens for the yet-unknown,
where users sign their names and make this place their own.
An email flies to prove they're real,
and tests confirm the deal.
```

### 鲁迅
```
从前，用户想要进门，却发现门上连个门铃都没有。今天我装了门铃，还附赠了验证码——毕竟，不是什么人都配进来的。
```

### haiku
```
New users arrive
Email proves identity
Tests guard the gateway
```

### changelog
```
Added: user registration endpoint (POST /api/auth/register)
Added: email verification service with token generation
Added: emailVerified and verificationToken fields to user model
Added: integration tests for registration flow
```

---

## 2. Bug Fix

**Scenario:** Fixed a race condition where concurrent API requests could create duplicate orders.

**Diff summary:**
- `src/services/order.ts` (modified, +8 -3 lines)
- `src/middleware/idempotency.ts` (new file, +34 lines)
- `tests/order.test.ts` (modified, +22 lines)

### conventional
```
fix(orders): prevent duplicate orders from concurrent requests

- Add idempotency key middleware to order creation endpoint
- Use database-level unique constraint on idempotency_key column
- Add concurrent request tests to reproduce and verify the fix
```

### emoji
```
🐛 Fix duplicate order creation from concurrent requests
🔧 Add idempotency key middleware
✅ Add concurrency tests for order creation
```

### poetic
```
Two threads raced to place one order twice,
now an idempotency key keeps things precise.
The database stands firm, unique constraint in hand,
no duplicate shall pass across this land.
```

### 鲁迅
```
两个请求同时冲进来抢着下单，仿佛菜市场的大妈。我不得不在门口立了块"幂等"的牌子，让它们排队进场。
```

### haiku
```
Two threads both raced in
One key now guards the gateway
Order stands alone
```

### changelog
```
Fixed: race condition causing duplicate orders from concurrent API requests
Added: idempotency key middleware for order creation
Added: database unique constraint on idempotency_key
Added: concurrent request reproduction tests
```

---

## 3. Refactoring

**Scenario:** Extracted shared validation logic from multiple controllers into a reusable validation middleware.

**Diff summary:**
- `src/middleware/validate.ts` (new file, +56 lines)
- `src/controllers/user.ts` (modified, +3 -28 lines)
- `src/controllers/product.ts` (modified, +3 -31 lines)
- `src/controllers/order.ts` (modified, +3 -25 lines)

### conventional
```
refactor(validation): extract shared validation logic into middleware

- Create reusable validate() middleware with schema-based validation
- Remove duplicated validation code from user, product, and order controllers
- Net reduction of 78 lines with improved consistency
```

### emoji
```
♻️ Extract shared validation into reusable middleware
🔥 Remove duplicated validation from 3 controllers
```

### poetic
```
Three controllers carried the same heavy load,
validation repeated down every road.
Now a single middleware bears that weight,
and the controllers breathe, clean and straight.
```

### 鲁迅
```
三个 controller 各自搬着同样的砖，干着同样的活，却互不相识。我把砖堆到了一处，告诉它们：从今往后，验证这事，有人统一管了。
```

### haiku
```
Shared code extracted
Three controllers now breathe free
One truth validates
```

### changelog
```
Added: reusable validate() middleware with JSON schema support
Changed: user, product, and order controllers to use shared validation middleware
Removed: duplicated validation logic from three controllers (net -78 lines)
```

---

## 4. Documentation

**Scenario:** Added API documentation with endpoint descriptions, request/response examples, and authentication guide.

**Diff summary:**
- `docs/api.md` (new file, +245 lines)
- `docs/authentication.md` (new file, +89 lines)
- `README.md` (modified, +15 -2 lines)

### conventional
```
docs: add API reference and authentication guide

- Create comprehensive API documentation with all endpoint descriptions
- Add authentication guide covering JWT flow and token refresh
- Update README with links to new documentation
```

### emoji
```
📝 Add API reference documentation
📝 Add authentication guide with JWT flow
📝 Update README with documentation links
```

### poetic
```
Where silence once filled the docs directory,
words now bloom to clear the mystery.
Every endpoint named, each token explained,
the README points the way for those who've been detained.
```

### 鲁迅
```
文档这东西，写的人觉得多余，不写的人觉得缺德。我选择了不做缺德的人——API 文档和认证指南，请查收。
```

### haiku
```
Docs fill the void now
Endpoints and tokens explained
README shows the way
```

### changelog
```
Added: API reference documentation (docs/api.md) with all endpoint descriptions
Added: authentication guide (docs/authentication.md) covering JWT and token refresh
Changed: README.md with links to new documentation sections
```

---

## 5. Mixed Changes

**Scenario:** Added dark mode support, fixed a CSS overflow bug, updated dependencies, and removed deprecated utility functions.

**Diff summary:**
- `src/themes/dark.css` (new file, +120 lines)
- `src/components/ThemeToggle.tsx` (new file, +45 lines)
- `src/components/Layout.tsx` (modified, +8 -2 lines)
- `src/styles/main.css` (modified, +3 -1 lines, overflow fix)
- `package.json` (modified, +4 -4 lines)
- `package-lock.json` (modified, large)
- `src/utils/deprecated.ts` (deleted, -89 lines)
- `src/utils/index.ts` (modified, +0 -3 lines)

### conventional
```
feat(ui): add dark mode support with theme toggle

- Add dark theme CSS and ThemeToggle component
- Integrate theme switcher into Layout component
- Fix CSS overflow bug in main stylesheet
- Remove deprecated utility functions (89 lines)
- Update dependencies: react 18.2->18.3, tailwind 3.3->3.4

BREAKING CHANGE: removed deprecated utility functions from src/utils/deprecated.ts
```

### emoji
```
✨ Add dark mode with theme toggle component
🐛 Fix CSS overflow bug in main stylesheet
📦 Update react (18.2->18.3) and tailwind (3.3->3.4)
🔥 Remove deprecated utility functions
```

### poetic
```
Darkness arrives as a welcome friend,
a toggle to shift when the daylight ends.
Overflow contained, no more spilling wide,
old utils removed -- they've had their ride.
Dependencies fresh, the packages bloom,
eight files touched to brighten and groom.
```

### 鲁迅
```
白天太亮了，我给它加了个暗色模式——权当是对光明的讽刺。顺手修了个 CSS 溢出的毛病，扔掉了一堆早该进坟墓的废弃函数，再给依赖们续了口气。八个文件，一场小型革命。
```

### haiku
```
Dark mode now exists
Old code swept, bugs fixed, deps fresh
Eight files tell the tale
```

### changelog
```
Added: dark mode theme (src/themes/dark.css) and ThemeToggle component
Fixed: CSS overflow issue in main stylesheet
Changed: Layout component to integrate theme switcher
Changed: updated react 18.2->18.3, tailwind 3.3->3.4
Removed: deprecated utility functions (src/utils/deprecated.ts, -89 lines)
```
