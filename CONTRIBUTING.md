# Contributing

Thanks for helping improve Triage.

## Local Setup

```bash
npm install
npm --prefix app install
cp .env.example app/.env
npm run dev
```

## Development Checks

Run the checks that match the files you changed:

```bash
npm run build
npm run test:contracts
```

## Pull Requests

- Keep changes focused and explain the user-facing impact.
- Include screenshots for UI changes.
- Include tests for contract behavior changes.
- Do not commit `.env`, local memory, generated build output, caches, private keys, or scratch files.

## Contract Changes

Contract edits should preserve deterministic GenLayer behavior, include direct-mode coverage for payout/report state changes, and pass:

```bash
./scripts/check-security-bounty.sh
```
