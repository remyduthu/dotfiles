## General

- Be extremely concise; sacrifice grammar for concision.
- Surface assumptions and confirm semantics before building. When requirements conflict, stop and ask.
- Push back when warranted rather than agreeing by default.
- Ship the smallest, most boring change that works. Add speculative abstractions, parallelism or options only when asked.
- Touch only what you're asked to touch, existing comments and style included.
- Readability is correctness: unclear code is a bug.
- Name things in full words (`repository`, not `repo`).
- Keep linters and tests green after each step; never skip a failing test.

## Comments And Documentation

- Explain what and why, keep implementation details out, and end every comment with a dot.

## Commits

- Use Conventional Commits with an uppercase subject (`feat(scope): Add…`) that completes "If applied, this commit will…".
- Explain why in the body; back performance and behavior claims with before/after numbers.
- Order footers alphabetically.
