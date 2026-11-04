// Shared helpers for the Haki chain scripts — Base Sepolia (TESTNET ONLY).
//
// Why createRequire: the SDK's ESM build hits a lodash named-export interop
// error on Node >= 22 (verified on Node 24); requiring the CommonJS build is
// stable across Node versions. Everything below uses the official
// @ethereum-attestation-service/eas-sdk (v2, ethers v6) exactly as documented:
//   https://github.com/ethereum-attestation-service/eas-sdk
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
const { EAS, SchemaEncoder, SchemaRegistry, NO_EXPIRATION } = require('@ethereum-attestation-service/eas-sdk');
const { ethers } = require('ethers');

export { EAS, SchemaEncoder, SchemaRegistry, NO_EXPIRATION, ethers };

// Contract addresses from the official Base docs (Base Sepolia == Base
// mainnet predeploy addresses):
// https://docs.base.org/specifications/reference/base-contracts
export const EAS_ADDRESS = '0x4200000000000000000000000000000000000021';
export const SCHEMA_REGISTRY_ADDRESS = '0x4200000000000000000000000000000000000020';
export const CHAIN_ID = 84532; // Base Sepolia
export const EXPLORER_TX = 'https://sepolia.basescan.org/tx/';
export const EASSCAN_ATTESTATION = 'https://base-sepolia.easscan.org/attestation/';

// The one schema Haki registers and attests against (schema.mjs / attest.mjs).
export const HAKI_SCHEMA = 'string assetId, string wallet, string verdict, string timestamp, string rulesProfile, string runId';
export const ZERO_ADDRESS = '0x0000000000000000000000000000000000000000';

const HERE = path.dirname(fileURLToPath(import.meta.url));

/** Minimal .env parser — no extra dependencies. Reads chain/.env only. */
export function loadEnv() {
  let raw;
  try {
    raw = readFileSync(path.join(HERE, '.env'), 'utf8');
  } catch {
    throw new Error('chain/.env not found — copy chain/.env.example to chain/.env and fill it in');
  }
  const env = {};
  for (const line of raw.split('\n')) {
    const m = line.match(/^\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$/);
    if (m) env[m[1]] = m[2].replace(/^["']|["']$/g, '').trim();
  }
  return env;
}

/** Build the faucet-funded throwaway signer. Testnet key ONLY. */
export function getSigner(env) {
  if (!env.BASE_SEPOLIA_RPC_URL) throw new Error('BASE_SEPOLIA_RPC_URL missing in chain/.env');
  if (!env.ATTESTER_PK) throw new Error('ATTESTER_PK missing in chain/.env (throwaway TESTNET key only)');
  const provider = new ethers.JsonRpcProvider(env.BASE_SEPOLIA_RPC_URL);
  return new ethers.Wallet(env.ATTESTER_PK, provider);
}

/** Hard guard: refuse to send anything anywhere except Base Sepolia. */
export async function assertBaseSepolia(signer) {
  const network = await signer.provider.getNetwork();
  if (Number(network.chainId) !== CHAIN_ID) {
    throw new Error(`wrong network: chainId ${network.chainId}, expected ${CHAIN_ID} (Base Sepolia). TESTNET ONLY — stopping.`);
  }
}
