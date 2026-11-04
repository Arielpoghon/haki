// Register the Haki attestation schema on Base Sepolia via the EAS
// SchemaRegistry. Run ONCE (the schema UID is deterministic).
//
// Usage:  npm run schema
// Output: SCHEMA_UID=0x...  -> copy that line into chain/.env
import {
  SchemaRegistry,
  SCHEMA_REGISTRY_ADDRESS,
  HAKI_SCHEMA,
  ZERO_ADDRESS,
  loadEnv,
  getSigner,
  assertBaseSepolia,
} from './lib.mjs';

const RESOLVER = ZERO_ADDRESS; // no resolver contract — data-only attestations
const REVOCABLE = true;

try {
  const env = loadEnv();
  const signer = getSigner(env);
  await assertBaseSepolia(signer);
  console.log('attester :', signer.address);
  console.log('network  : Base Sepolia (chainId 84532)');

  const registry = new SchemaRegistry(SCHEMA_REGISTRY_ADDRESS).connect(signer);

  // SchemaRegistry.getSchemaUID is a static, deterministic computation
  // (keccak of schema + resolver + revocable) — verified against the SDK types.
  const schemaUID = SchemaRegistry.getSchemaUID(HAKI_SCHEMA, RESOLVER, REVOCABLE);
  console.log('schema   :', HAKI_SCHEMA);

  const existing = await registry.getSchema({ uid: schemaUID });
  if (existing.uid === schemaUID) {
    console.log('status   : already registered — nothing to do');
  } else {
    const tx = await registry.register({
      schema: HAKI_SCHEMA,
      resolverAddress: RESOLVER,
      revocable: REVOCABLE,
    });
    console.log('tx       :', tx.data.hash);
    const registeredUID = await tx.wait();
    if (registeredUID !== schemaUID) {
      console.log('note     : tx returned UID', registeredUID);
    }
    console.log('status   : registered');
  }

  console.log('\nSCHEMA_UID=' + schemaUID);
  console.log('-> paste this line into chain/.env');
} catch (err) {
  console.error('ERROR:', err.message);
  process.exit(1);
}
