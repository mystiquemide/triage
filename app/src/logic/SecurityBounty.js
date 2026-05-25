import { abi } from "genlayer-js";
import { encodeFunctionData, fromHex } from "viem";
import { ensureStudioNetwork, getWalletProvider } from "../services/genlayer";

const STUDIO_CHAIN_ID = 61999;
const FALLBACK_GAS = 500000n;
const GAS_BUFFER_PERCENT = 20n;
const EVM_WALLET_KEY = "sb_evm_wallet";
const ZERO_ADDRESS = "0x0000000000000000000000000000000000000000";
const DIRECT_STUDIO_RPC_URL = import.meta.env.VITE_STUDIO_URL || "https://studio.genlayer.com/api";
const PRODUCTION_RPC_PATH = "/api/genlayer-rpc";
const HIDDEN_PROGRAM_IDS = new Set(["codex_smoke_163446_61999"]);

const toBigInt = (value, fallback = 0n) => {
  if (value == null) return fallback;
  try {
    return BigInt(value);
  } catch {
    return fallback;
  }
};

const toNumber = (value) => Number(toBigInt(value));
const toHex = (value) => `0x${toBigInt(value).toString(16)}`;
const at = (record, key, index, fallback = "") => {
  if (record instanceof Map) return record.get(key) ?? record.get(index) ?? fallback;
  return record?.[key] ?? record?.[index] ?? fallback;
};

const getReadRpcUrl = () => {
  if (typeof window === "undefined") return DIRECT_STUDIO_RPC_URL;
  const isLocalhost = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  return isLocalhost ? DIRECT_STUDIO_RPC_URL : `${window.location.origin}${PRODUCTION_RPC_PATH}`;
};

const makeCalldataObject = (method, args = []) => {
  return { method, args };
};

const rpcRequest = (method, params) => new Promise((resolve, reject) => {
  if (typeof XMLHttpRequest === "undefined") {
    reject(new Error("Browser RPC transport is unavailable."));
    return;
  }

  const xhr = new XMLHttpRequest();
  xhr.open("POST", getReadRpcUrl(), true);
  xhr.setRequestHeader("content-type", "application/json");
  xhr.onload = () => {
    try {
      const payload = JSON.parse(xhr.responseText || "{}");
      if (payload.error) {
        reject(new Error(payload.error.message || "GenLayer RPC error"));
        return;
      }
      resolve(payload.result);
    } catch (error) {
      reject(error);
    }
  };
  xhr.onerror = () => reject(new Error("GenLayer RPC request failed."));
  xhr.send(JSON.stringify({ jsonrpc: "2.0", id: Date.now(), method, params }));
});

const toBool = (value) => {
  if (value === true || value === 1 || value === 1n) return true;
  if (typeof value === "string") return value.toLowerCase() === "true" || value === "1";
  return false;
};

const normalizeProgram = (program) => {
  const hasOwner = Array.isArray(program) && program.length >= 11;
  const offset = hasOwner ? 1 : 0;
  return {
    id: at(program, "id", 0),
    owner: at(program, "owner", 1),
    protocol_name: at(program, "protocol_name", 1 + offset),
    contract_address: at(program, "contract_address", 2 + offset),
    description: at(program, "description", 3 + offset),
    program_metadata: at(program, "program_metadata", 4 + offset),
    reward_pool: String(at(program, "reward_pool", 5 + offset, "0")),
    escrow_balance: String(at(program, "escrow_balance", 6 + offset, "0")),
    max_payout: String(at(program, "max_payout", 7 + offset, "0")),
    is_funded: toBool(at(program, "is_funded", 8 + offset, false)),
    is_active: toBool(at(program, "is_active", 9 + offset, true)),
    created_at: at(program, "created_at", 10 + offset),
  };
};

const normalizeReport = (report) => {
  const hasLinks = Array.isArray(report) && Array.isArray(report[5]);
  const offset = hasLinks ? 1 : 0;
  const payoutOffset = offset + (Array.isArray(report) && report.length >= 14 ? 2 : 0);
  return {
    id: at(report, "id", 0),
    program_id: at(report, "program_id", 1) || at(report, "bounty_program_id", 1),
    submitter: at(report, "submitter", 2),
    title: at(report, "title", 3),
    description: at(report, "description", 4),
    affected_code_links: at(report, "affected_code_links", 5, []),
    report_metadata: at(report, "report_metadata", 5 + offset),
    severity_vote: at(report, "severity_vote", 6 + offset),
    status: at(report, "status", 7 + offset),
    evaluated_severity: at(report, "evaluated_severity", 8 + offset),
    reward: String(at(report, "reward", 9 + offset, "0")),
    payout_status: String(at(report, "payout_status", 10 + offset, "")),
    payout_attempts: String(at(report, "payout_attempts", 11 + offset, "0")),
    created_at: at(report, "created_at", 10 + payoutOffset),
    resolved_at: at(report, "resolved_at", 11 + payoutOffset),
  };
};

const normalizeVulnerability = (vuln) => {
  const hasDescriptionHash = Array.isArray(vuln) && vuln.length >= 8;
  const offset = hasDescriptionHash ? 1 : 0;
  return {
    id: at(vuln, "id", 0),
    contract_address: at(vuln, "contract_address", 1),
    title: at(vuln, "title", 2),
    severity: at(vuln, "severity", 3),
    reporter: at(vuln, "reporter", 4 + offset),
    program_id: at(vuln, "program_id", 5 + offset),
    timestamp: at(vuln, "timestamp", 6 + offset),
  };
};

const shouldFallbackToLocalSigner = (error) => {
  const text = `${error?.message || ""} ${error?.details || ""} ${error?.shortMessage || ""}`;
  return [
    "eth_fillTransaction",
    "Invalid transaction data",
    "Method not found",
    "MethodNotFound",
    "MethodNotSupported",
    "Unsupported method",
  ].some(fragment => text.includes(fragment));
};

class SecurityBounty {
  constructor(contractAddress, client) {
    this.address = contractAddress;
    this.client = client;
  }

  setClient(c) { this.client = c; }

  async _read(fn, args = []) {
    const encodedData = abi.calldata.encode(makeCalldataObject(fn, args));
    const data = abi.transactions.serializeOne(encodedData);
    const from = this.client?.account?.address || ZERO_ADDRESS;
    const result = await rpcRequest("eth_call", [{ to: this.address, from, data }, "latest"]);
    if (!result) return [];
    return abi.calldata.decode(fromHex(result, "bytes")) || [];
  }

  async _write(fn, args = [], value = 0n) {
    const senderAccount = this.client.account;
    if (!senderAccount?.signTransaction) {
      throw new Error("No local GenLayer signer found. Connect your wallet again to create a StudioNet signer.");
    }

    await this.client.initializeConsensusSmartContract();
    const consensus = this.client.chain.consensusMainContract;
    if (!consensus?.address || !consensus?.abi) {
      throw new Error("StudioNet consensus contract is not available yet. Try again in a moment.");
    }

    const calldata = abi.calldata.encode({ method: fn, args });
    const txData = abi.transactions.serialize([calldata, false]);
    const txValue = toBigInt(value);
    const txValueHex = toHex(txValue);
    const data = encodeFunctionData({
      abi: consensus.abi,
      functionName: "addTransaction",
      args: [
        senderAccount.address,
        this.address,
        this.client.chain.defaultNumberOfInitialValidators,
        this.client.chain.defaultConsensusMaxRotations,
        txData,
      ],
    });

    const nonce = await this.client.request({
      method: "eth_getTransactionCount",
      params: [senderAccount.address, "latest"],
    });

    let gas = FALLBACK_GAS;
    try {
      const estimatedGas = toBigInt(await this.client.request({
        method: "eth_estimateGas",
        params: [{
          from: senderAccount.address,
          to: consensus.address,
          data,
          value: txValueHex,
        }],
      }), FALLBACK_GAS);
      gas = estimatedGas + (estimatedGas * GAS_BUFFER_PERCENT / 100n);
    } catch (error) {
      console.warn("Gas estimation failed, using fallback gas", error);
    }

    let gasPrice = 1n;
    try {
      gasPrice = toBigInt(await this.client.request({ method: "eth_gasPrice" }), 1n);
    } catch (error) {
      console.warn("Gas price fetch failed, using fallback gas price", error);
    }

    const walletProvider = typeof window !== "undefined" ? await getWalletProvider() : null;
    const walletAddress = typeof localStorage !== "undefined" ? localStorage.getItem(EVM_WALLET_KEY) : null;
    if (walletProvider?.request && walletAddress) {
      try {
        await ensureStudioNetwork(walletProvider);
        const hash = await walletProvider.request({
          method: "eth_sendTransaction",
          params: [{
            from: walletAddress,
            to: consensus.address,
            data,
            gas: toHex(gas),
            gasPrice: toHex(gasPrice),
            value: txValueHex,
          }],
        });
        return { hash, signer: "browser-wallet" };
      } catch (error) {
        if (error?.code === 4001 || !shouldFallbackToLocalSigner(error)) throw error;
        if (txValue > 0n) {
          throw new Error("Funding requires a browser wallet transaction with GEN value. Please fund your wallet on StudioNet and try again.");
        }
        console.warn("Browser wallet transaction path failed; falling back to local GenLayer signer.", error);
      }
    }

    if (txValue > 0n) {
      throw new Error("Funding requires a connected browser wallet. The local StudioNet signer cannot escrow GEN value.");
    }

    const serializedTransaction = await senderAccount.signTransaction({
      chainId: STUDIO_CHAIN_ID,
      type: "legacy",
      nonce: toNumber(nonce),
      to: consensus.address,
      data,
      gas,
      gasPrice,
      value: txValue,
    });

    const hash = await this.client.request({
      method: "eth_sendRawTransaction",
      params: [serializedTransaction],
    });
    return { hash, signer: "local-genlayer" };
  }

  createProgram(protoName, ca, desc, pool, max, metadata = "", escrowAmount = 0n) {
    return this._write("create_program", [
      protoName,
      ca,
      desc,
      pool,
      max,
      metadata,
    ], escrowAmount);
  }
  fundProgram(pid, amount)                           { return this._write("fund_program", [pid], amount); }
  deactivateProgram(pid)                            { return this._write("deactivate_program", [pid]); }
  submitReport(pid, title, desc, links, sev, metadata = "") {
    return this._write("submit_report", [
      pid,
      title,
      desc,
      links,
      sev,
      metadata,
    ]);
  }
  evaluateReport(rid)                               { return this._write("evaluate_report",    [rid]); }
  retryPayout(rid)                                  { return this._write("retry_payout",       [rid]); }

  async listPrograms() {
    const programs = await this._read("list_programs");
    return (Array.isArray(programs) ? programs : [])
      .map(normalizeProgram)
      .filter(p => p.id && p.is_active && !HIDDEN_PROGRAM_IDS.has(p.id));
  }
  async getProgram(pid) {
    return normalizeProgram(await this._read("get_program", [pid]));
  }
  async listReports() {
    const reports = await this._read("list_reports");
    return (Array.isArray(reports) ? reports : []).map(normalizeReport).filter(r => r.id);
  }
  async getReport(rid) {
    return normalizeReport(await this._read("get_report", [rid]));
  }
  async getHackerReports(addr) {
    const reports = await this._read("get_hacker_reports", [addr]);
    return (Array.isArray(reports) ? reports : []).map(normalizeReport).filter(r => r.id);
  }
  async getVulnerabilityRegistry() {
    const vulns = await this._read("get_vulnerability_registry");
    return (Array.isArray(vulns) ? vulns : []).map(normalizeVulnerability).filter(v => v.id);
  }
  async getVulnerabilitiesByContract(ca) {
    const vulns = await this._read("get_vulnerabilities_by_contract", [ca]);
    return (Array.isArray(vulns) ? vulns : []).map(normalizeVulnerability).filter(v => v.id);
  }
}

export default SecurityBounty;
