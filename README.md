# README Agent (LangChain + FastAPI, Render-deployable)

This service listens to **GitHub push** webhooks, summarizes code changes with **LangChain**/**OpenAI**, and auto-updates your repository's `README.md`. Designed to be minimal and easy to deploy on **Render**.

## How it works
1. GitHub sends a **push** event to `/webhook`.
2. The server calls GitHub **Compare API** to get a unified diff between the previous and latest commits.
3. A LangChain `ChatOpenAI` model generates a full, updated `README.md` based on user-facing changes.
4. The service clones your repo, writes the new README, and pushes a commit.

> For public repos, reading diffs doesn't need auth. Pushing changes uses a single **GITHUB_PAT** (env var).

## Environment variables
- `OPENAI_API_KEY` — required for the LLM.
- `GITHUB_PAT` — GitHub token with repo **contents: write** to push commits.
- `COMMIT_BACK` — "true" to push changes; "false" to only compute suggestions.
- `DEFAULT_BRANCH` — branch to update (default "main").

## Endpoints
- `GET /health` — health check.
- `POST /webhook` — GitHub webhook (push event only).

## Security
For simplicity, the default project doesn't validate webhook signatures. In production, verify `X-Hub-Signature-256`.

## License
MIT

<!-- auto: 2025-10-18T04:42:41.936198Z 7c252a6 -->

<!-- auto: 2025-10-18T04:43:00.483359Z 531c72c -->

<!-- auto: 2025-10-18T04:43:13.920506Z 7b44ed3 -->

<!-- auto: 2025-10-18T04:43:31.491774Z 7f0ee30 -->

<!-- auto: 2025-10-18T04:43:41.403344Z 5e062d3 -->

<!-- auto: 2025-10-18T04:44:00.050777Z c20aafe -->

<!-- auto: 2025-10-18T05:13:40.009191Z 9ad316f -->

<!-- auto: 2025-10-18T05:14:01.514214Z a7a801e -->

<!-- auto: 2025-10-18T05:14:11.313413Z ea62b98 -->

<!-- auto: 2025-10-18T05:14:33.846772Z cb49321 -->


<!-- auto: 2025-10-18T05:14:47.779392Z 8a99868 -->
