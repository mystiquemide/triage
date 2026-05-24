import { createClient, createAccount as genlayerAccount, generatePrivateKey } from "genlayer-js";
import { simulator } from "genlayer-js/chains";

const KEY = "sb_wallet";
const EVM_KEY = "sb_evm_wallet";
const STUDIO_CHAIN_ID = 61999;
const STUDIO_CHAIN_ID_HEX = `0x${STUDIO_CHAIN_ID.toString(16)}`;
const STUDIO_EXPLORER_URL = "https://genlayer-explorer.vercel.app";
const DIRECT_STUDIO_RPC_URL = import.meta.env.VITE_STUDIO_URL || "https://studio.genlayer.com/api";
const PRODUCTION_RPC_PATH = "/api/genlayer-rpc";

function getStudioRpcUrl() {
  if (typeof window === "undefined") return DIRECT_STUDIO_RPC_URL;

  const isLocalhost = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  if (isLocalhost) return DIRECT_STUDIO_RPC_URL;

  return `${window.location.origin}${PRODUCTION_RPC_PATH}`;
}

export function getAccount() {
  const pk = localStorage.getItem(KEY);
  if (!pk) return null;
  return genlayerAccount(pk);
}

export function createAccount() {
  const pk = generatePrivateKey();
  localStorage.setItem(KEY, pk);
  return genlayerAccount(pk);
}

export function clearAccount() {
  localStorage.removeItem(KEY);
  localStorage.removeItem(EVM_KEY);
}

export function getConnectedEvmAddress() {
  return localStorage.getItem(EVM_KEY);
}

async function switchToStudioNetwork(provider) {
  try {
    await provider.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId: STUDIO_CHAIN_ID_HEX }],
    });
  } catch (error) {
    if (error?.code !== 4902) throw error;

    await provider.request({
      method: "wallet_addEthereumChain",
      params: [{
        chainId: STUDIO_CHAIN_ID_HEX,
        chainName: "GenLayer Studio Network",
        nativeCurrency: {
          name: "GEN Token",
          symbol: "GEN",
          decimals: 18,
        },
        rpcUrls: [getStudioRpcUrl()],
        blockExplorerUrls: [STUDIO_EXPLORER_URL],
      }],
    });

    await provider.request({
      method: "wallet_switchEthereumChain",
      params: [{ chainId: STUDIO_CHAIN_ID_HEX }],
    });
  }
}

export async function connectEvmWallet() {
  const provider = window.ethereum;
  if (!provider?.request) {
    throw new Error("No EVM wallet found. Please install MetaMask or another browser wallet.");
  }

  const accounts = await provider.request({ method: "eth_requestAccounts" });
  const address = accounts?.[0];
  if (!address) throw new Error("No wallet account selected.");

  await switchToStudioNetwork(provider);

  localStorage.setItem(EVM_KEY, address);
  return address;
}

export async function confirmWalletAction({ action, details, contractAddress }) {
  const provider = window.ethereum;
  const address = getConnectedEvmAddress();
  if (!provider?.request || !address) {
    throw new Error("Connect your wallet before sending a transaction.");
  }

  await switchToStudioNetwork(provider);

  const message = [
    "SecurityBounty transaction confirmation",
    "",
    `Action: ${action}`,
    `Wallet: ${address}`,
    `Network: GenLayer Studio Network (${STUDIO_CHAIN_ID})`,
    `Contract: ${contractAddress}`,
    "",
    details,
    "",
    "Signing this message confirms you want the app to submit this GenLayer StudioNet transaction.",
  ].join("\n");

  await provider.request({
    method: "personal_sign",
    params: [message, address],
  });
}

export function setConnectedEvmAddress(address) {
  if (address) localStorage.setItem(EVM_KEY, address);
  else localStorage.removeItem(EVM_KEY);
}

export function createBountyClient(account = null) {
  return createClient({
    chain: simulator,
    account,
    endpoint: getStudioRpcUrl(),
  });
}
