# CLI Start

Give the coding agent this instruction:

> Read `AGENTS.md` and every document listed under its **Required implementation specs**. Inspect the repository before changing anything. Then implement only `docs/implementation/FIRST_VERTICAL_SLICE.md` in the documented order. Preserve hardware independence. If a decision would change a product principle, domain boundary, platform contract or selected technology stack, stop and propose an ADR instead of silently deciding it. Keep tests green and update documentation when contracts change.

Before code generation, the agent should first report:
1. its understanding of the architecture;
2. the concrete file/module plan;
3. unresolved technology choices needed for the slice;
4. any contradiction it finds in the documents.
