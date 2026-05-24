# Deployment

## Prerequisites

- Node.js 20+
- npm 10+
- Python 3.12+
- GenLayer CLI
- A readable GenLayer StudioNet contract address
- Optional: Vercel CLI for hosted frontend deployment

## Environment Variables

Copy the example file into the frontend app:

```bash
cp .env.example app/.env
```

| Variable | Required | Description |
|---|---:|---|
| `VITE_CONTRACT_ADDRESS` | Yes | StudioNet `SecurityBounty` contract address. |
| `VITE_STUDIO_URL` | Yes | StudioNet RPC URL. |

Use placeholder values in committed examples only. Never commit a real `.env`.

## Contract Verification

```bash
./scripts/check-security-bounty.sh
```

This runs GenVM lint/validation and direct-mode tests for `contracts/security_bounty.py`.

## Contract Deployment

```bash
genlayer network set studionet
genlayer deploy --contract contracts/security_bounty.py
```

After deployment, wait for the transaction to reach `ACCEPTED`, then verify reads:

```bash
genlayer call <contract-address> list_programs
```

Only update `VITE_CONTRACT_ADDRESS` after the new contract is accepted and readable.

## Local Production Build

```bash
npm install
npm --prefix app install
npm run build
npm run preview
```

## Vercel Deployment

Current production frontend:

- [https://triage-weld.vercel.app](https://triage-weld.vercel.app)

The frontend lives in `app/`.

```bash
vercel link
vercel env add VITE_CONTRACT_ADDRESS
vercel env add VITE_STUDIO_URL
vercel deploy
vercel deploy --prod
```

Recommended Vercel settings:

- Root directory: `app`
- Build command: `npm run build`
- Output directory: `dist`

## Post-Deploy Verification

- Visit the deployed app.
- Confirm the configured StudioNet contract address is readable.
- Connect a wallet.
- Load programs and reports.
- Create a test program only on a test network or StudioNet environment intended for demos.
- Submit and inspect a report.

## Troubleshooting

### StudioNet Deploy Stays Pending

Keep the frontend pointed at the last known readable contract. Do not switch `VITE_CONTRACT_ADDRESS` to a precomputed address until a read call succeeds.

### Wallet Shows 0 GEN

StudioNet is gasless for normal interaction, but funded bounty escrow depends on the network and wallet setup. Verify the wallet is connected to GenLayer Studio Network.

### Vercel Build Fails

Check that Vercel uses `app` as the root directory and that both Vite environment variables are configured.
