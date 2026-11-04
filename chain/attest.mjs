// Attest a Haki screening result on Base Sepolia via EAS. TESTNET ONLY.
//
// Usage:
//   npm run attest -- '{"assetId":"KE-TB-2030","wallet":"0xabc...","verdict":"ALLOW","timestamp":"2026-11-05T12:00:00Z","rulesProfile":"KE","runId":"run-001"}'
//
// All six fields are required (they must match the registered schema).
// Output: tx hash + Basescan link, attestation UID + easscan link.
import {
  EAS,
  SchemaEncoder,
  NO_EXPIRATION,
  EAS_ADDRESS,
  EXPLORER_TX,
  EASSCAN_ATTESTATION,
  HAKI_SCHEMA,
  loadEnv,
  getSigner,
  assertBaseSepolia,
} from './lib.mjs';

function die(msg) {
  console.error('ERROR:', msg);
  process.exit(1);
}

const arg = process.argv[2];
if (!arg) {
  die("usage: npm run attest -- '{\"assetId\":..., \"wallet\":..., \"verdict\":..., \"timestamp\":..., \"rulesProfile\":..., \"runId\":...}'");
}

let payload;
try {
  payload = JSON.parse(arg);
} catch (err) {
  die('payload is not valid JSON: ' + err.message);
}
for (const field of ['assetId', 'wallet', 'verdict', 'timestamp', 'rulesProfile', 'runId']) {
  if (!payload[field] || typeof payload[field] !== 'string') {
    die(`payload missing string field: ${field}`);
  }
}
if (!payload.wallet.startsWith('0x')) die('wallet must be a 0x address');

try {
  const env = loadEnv();
  if (!env.SCHEMA_UID) die('SCHEMA_UID missing in chain/.env — run `npm run schema` first');
  const signer = getSigner(env);
  await assertBaseSepolia(signer);

  const eas = new EAS(EAS_ADDRESS).connect(signer);
  const encoder = new SchemaEncoder(HAKI_SCHEMA);
  const encodedData = encoder.encodeData([
    { name: 'assetId', type: 'string', value: payload.assetId },
    { name: 'wallet', type: 'string', value: payload.wallet },
    { name: 'verdict', type: 'string', value: payload.verdict },
    { name: 'timestamp', type: 'string', value: payload.timestamp },
    { name: 'rulesProfile', type: 'string', value: payload.rulesProfile },
    { name: 'runId', type: 'string', value: payload.runId },
  ]);

  console.log('attesting:', payload.assetId, 'x', payload.wallet, '=>', payload.verdict);
  const tx = await eas.attest({
    schema: env.SCHEMA_UID,
    data: {
      recipient: payload.wallet,
      expirationTime: NO_EXPIRATION,
      revocable: true,
      data: encodedData,
    },
  });
  console.log('tx hash  :', tx.data.hash);
  console.log('basescan :', EXPLORER_TX + tx.data.hash);

  const attestationUID = await tx.wait();
  console.log('UID      :', attestationUID);
  console.log('easscan  :', EASSCAN_ATTESTATION + attestationUID);

  const attestation = await eas.getAttestation(attestationUID);
  console.log('attester :', attestation.attester);
  console.log('recipient:', attestation.recipient);
  console.log('time     :', attestation.time);
} catch (err) {
  die(err.message);
}
