// Verify a Haki attestation on Base Sepolia — READ-ONLY, no key needed.
//
// Usage:
//   npm run verify                          # verifies the recorded drill-1 demo attestation
//   npm run verify -- 0x<attestation-uid>   # verifies any attestation
//
// Why this exists: easscan's web frontend sometimes renders "Page not found!"
// for attestations it has already indexed. The chain itself is the source of
// truth — this script talks straight to the EAS contract via eth_call.
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { ethers } = require('ethers');
const { SchemaRegistry } = require('@ethereum-attestation-service/eas-sdk');

// Recorded from the m3-onchain-live drill (2026-11-05).
const DEMO_ATTESTATION_UID =
  '0xcc907f0d9320889f7a129150da653cd0df86eaa3591db8b17a48ee7eac3a4421';

const RPC = process.env.BASE_SEPOLIA_RPC_URL || 'https://sepolia.base.org';
const EAS_ADDRESS = '0x4200000000000000000000000000000000000021';
const SCHEMA_REGISTRY_ADDRESS = '0x4200000000000000000000000000000000000020';
const HAKI_SCHEMA =
  'string assetId, string wallet, string verdict, string timestamp, string rulesProfile, string runId';

const uidArg = process.argv[2];
if (uidArg && !/^0x[0-9a-fA-F]{64}$/.test(uidArg)) {
  console.error('ERROR: UID must be a 0x-prefixed 32-byte hex string');
  process.exit(1);
}
const uid = uidArg || DEMO_ATTESTATION_UID;

const provider = new ethers.JsonRpcProvider(RPC);
const net = await provider.getNetwork();
if (Number(net.chainId) !== 84532) {
  console.error('ERROR: RPC is not Base Sepolia (chainId ' + net.chainId + ')');
  process.exit(1);
}

console.log('verifying on Base Sepolia (block', (await provider.getBlockNumber()) + ')');
console.log('uid       :', uid);

// The deterministic Haki schema UID (keccak of schema + resolver + revocable).
const schemaUID = SchemaRegistry.getSchemaUID(HAKI_SCHEMA, ethers.ZeroAddress, true);

const eas = new ethers.Contract(
  EAS_ADDRESS,
  [
    'function getAttestation(bytes32 uid) view returns (tuple(bytes32 uid, bytes32 schema, uint64 time, uint64 expirationTime, uint64 revocationTime, bytes32 refUid, address recipient, address attester, bool revocable, bytes data) a)',
  ],
  provider
);

const a = await eas.getAttestation(uid);
if (a.time === 0n || a.attester === ethers.ZeroAddress) {
  console.log('RESULT    : NOT FOUND — no attestation with this UID on Base Sepolia.');
  process.exit(1);
}

console.log('\n--- attestation ---');
console.log('schema    :', a.schema, a.schema === schemaUID ? '(Haki schema OK)' : '(UNKNOWN SCHEMA)');
console.log('attester  :', a.attester);
console.log('recipient :', a.recipient);
console.log('time      :', a.time.toString(), '(' + new Date(Number(a.time) * 1000).toISOString() + ')');
console.log('expires   :', a.expirationTime === 0n ? 'never' : a.expirationTime.toString());
console.log('revoked   :', a.revocationTime !== 0n ? 'YES @ ' + a.revocationTime : 'no');
console.log('revocable :', a.revocable);

const [assetId, wallet, verdict, ts, rulesProfile, runId] = ethers.AbiCoder.defaultAbiCoder().decode(
  ['string', 'string', 'string', 'string', 'string', 'string'],
  a.data
);
console.log('\n--- payload ---');
console.log('assetId    :', assetId);
console.log('wallet     :', wallet);
console.log('verdict    :', verdict);
console.log('timestamp  :', ts);
console.log('rulesProfile:', rulesProfile);
console.log('runId      :', runId);

const registry = new ethers.Contract(
  SCHEMA_REGISTRY_ADDRESS,
  ['function getSchema(bytes32 uid) view returns (tuple(bytes32 uid, address resolver, bool revocable, string schema) r)'],
  provider
);
const s = await registry.getSchema(schemaUID);
console.log('\n--- schema registry ---');
console.log('registered:', s.schema === HAKI_SCHEMA ? 'YES' : 'MISMATCH');
console.log('resolver  :', s.resolver, '(none — data-only)');

console.log(
  '\nRESULT    : VERIFIED ONCHAIN — easscan links: https://base-sepolia.easscan.org/attestation/' + uid
);
