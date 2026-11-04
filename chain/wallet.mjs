// Generate a throwaway wallet for the Base Sepolia day-1 drill. TESTNET ONLY.
//
// Usage: node wallet.mjs
// Prints an address + private key. Put the key ONLY into chain/.env
// (gitignored) as ATTESTER_PK, fund the address from a Base Sepolia faucet,
// and never use this wallet for anything of value.
import { ethers } from './lib.mjs';

const wallet = ethers.Wallet.createRandom();
console.log('address:       ', wallet.address);
console.log('private key:   ', wallet.privateKey);
console.log('');
console.log('1) put the private key in chain/.env as ATTESTER_PK');
console.log('2) fund the address from a Base Sepolia faucet (testnet ETH only)');
console.log('3) this is a THROWAWAY testnet wallet — never fund it with real funds');
