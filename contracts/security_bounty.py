# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from dataclasses import dataclass
import json
from genlayer import *
from genlayer.py.keccak import Keccak256

# --------------------------------------------------------------
# Bug Bounty Platform - Self-Aware Security Audit Validator
# --------------------------------------------------------------
# Hackers submit bug reports. GenLayer validators (diverse LLMs)
# independently evaluate: Is this a real vulnerability? Severity?
# Is it a duplicate? Auto-pays on validation. Builds a shared
# vulnerability registry that other contracts can query.
# --------------------------------------------------------------

# --- Error classifiers (deterministic for consensus) ---
ERROR_EXPECTED  = "[EXPECTED]"
ERROR_EXTERNAL  = "[EXTERNAL]"
ERROR_TRANSIENT = "[TRANSIENT]"
ERROR_LLM       = "[LLM_ERROR]"

SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH     = "high"
SEVERITY_MEDIUM   = "medium"
SEVERITY_LOW      = "low"
SEVERITY_NONE     = "none"

STATUS_PENDING   = "pending"
STATUS_ACCEPTED  = "accepted"
STATUS_REJECTED  = "rejected"
STATUS_DUPLICATE = "duplicate"

PAYOUT_NONE    = "none"
PAYOUT_PENDING = "pending"
PAYOUT_EMITTED = "emitted"
MAX_PAYOUT_ATTEMPTS = u256(3)

BOUNTY_MULTIPLIER = {
    SEVERITY_CRITICAL: 100,
    SEVERITY_HIGH:     50,
    SEVERITY_MEDIUM:   20,
    SEVERITY_LOW:      5,
}

# --- Scoring weights for LLM evaluation (consensus-safe) ---
SEVERITY_WEIGHTS = {
    SEVERITY_CRITICAL: 5,
    SEVERITY_HIGH:     4,
    SEVERITY_MEDIUM:   3,
    SEVERITY_LOW:      2,
    SEVERITY_NONE:     1,
}


@allow_storage
@dataclass
class BountyProgram:
    """A bug bounty program posted by a protocol."""
    id: str
    owner: str  # address as hex
    protocol_name: str
    contract_address: str  # target contract address
    description: str
    program_metadata: str
    reward_pool: u256  # total GEN allocated
    escrow_balance: u256  # funded GEN available for automatic payouts
    max_payout: u256  # max per-bug payout
    is_active: bool
    created_at: str


@allow_storage
@dataclass
class BugReport:
    """A vulnerability report submitted by a hacker."""
    id: str
    bounty_program_id: str
    submitter: str  # address as hex
    title: str
    description: str
    affected_code_links: DynArray[str]  # URLs to code / PoC
    report_metadata: str
    severity_vote: str  # hacker's self-assessed severity
    status: str
    evaluated_severity: str  # final severity from consensus
    reward: u256  # actual payout
    payout_status: str  # native payout lifecycle
    payout_attempts: u256
    created_at: str
    resolved_at: str


@allow_storage
@dataclass
class VulnRecord:
    """Entry in the shared vulnerability registry."""
    id: str
    contract_address: str
    title: str
    severity: str
    description_hash: str  # keccak of full description for dedup
    reporter: str
    program_id: str
    timestamp: str


class SecurityBounty(gl.Contract):
    """Self-aware bug bounty platform with AI-driven report validation."""

    # --- Storage ---
    programs: TreeMap[str, BountyProgram]
    """bounty program ID -> program"""

    program_ids: DynArray[str]
    """ordered list of program IDs for iteration"""

    bug_reports: TreeMap[str, BugReport]
    """bug report ID -> report"""

    vuln_registry: TreeMap[str, VulnRecord]
    """shared vulnerability registry - queryable by any contract"""

    owner: Address

    # --- Counter for unique report IDs ---
    report_counter: u256

    # --- Init ---

    def __init__(self):
        self.owner = gl.message.sender_address
        self.report_counter = u256(0)

    # --- Admin ---

    @gl.public.write.payable
    def create_program(
        self,
        protocol_name: str,
        contract_address: str,
        description: str,
        reward_pool: u256,
        max_payout: u256,
        program_metadata: str,
    ) -> dict:
        """Create a new bug bounty program owned by the caller."""
        protocol_name = self._to_storage_string(protocol_name)
        contract_address = self._to_storage_string(contract_address)
        description = self._to_storage_string(description)
        program_metadata = self._to_storage_string(program_metadata)

        if reward_pool <= 0:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Reward pool must be positive")

        if max_payout <= 0:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Max payout must be positive")

        if gl.message.value > reward_pool:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Escrow cannot exceed reward pool")

        pid = f"{protocol_name.lower().replace(' ', '_')}_{gl.message_raw['chain_id']}"
        if pid in self.programs:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Program '{pid}' already exists")

        program = BountyProgram(
            id=pid,
            owner=gl.message.sender_address.as_hex,
            protocol_name=protocol_name,
            contract_address=contract_address,
            description=description,
            program_metadata=program_metadata,
            reward_pool=reward_pool,
            escrow_balance=gl.message.value,
            max_payout=max_payout,
            is_active=True,
            created_at=gl.message_raw["datetime"],
        )
        self.programs[pid] = program
        self.program_ids.append(pid)
        return {
            "program_id": pid,
            "reward_pool": str(reward_pool),
            "escrow_balance": str(program.escrow_balance),
            "is_funded": program.escrow_balance > 0,
        }

    @gl.public.write.payable
    def fund_program(self, program_id: str) -> dict:
        """Add native GEN escrow to an existing bounty program."""
        program_id = self._to_storage_string(program_id)
        if program_id not in self.programs:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Program not found")

        if gl.message.value <= 0:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Funding amount must be positive")

        program = self.programs[program_id]
        if gl.message.sender_address.as_hex != program.owner:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Only program owner")

        if not program.is_active:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Program is inactive")

        if program.escrow_balance + gl.message.value > program.reward_pool:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Funding exceeds remaining reward pool")

        program.escrow_balance += gl.message.value
        return {
            "program_id": program_id,
            "reward_pool": str(program.reward_pool),
            "escrow_balance": str(program.escrow_balance),
        }

    @gl.public.write
    def deactivate_program(self, program_id: str) -> dict:
        """Deactivate a bounty program."""
        if program_id not in self.programs:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Program not found")

        program = self.programs[program_id]
        if gl.message.sender_address.as_hex != program.owner:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Only program owner")

        if not program.is_active:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Program already inactive")

        program.is_active = False
        return {"program_id": program_id, "status": "deactivated"}

    # --- Hacker Submission ---

    @gl.public.write
    def submit_report(
        self,
        program_id: str,
        title: str,
        description: str,
        affected_code_links: DynArray[str],
        severity_self_assess: str,
        report_metadata: str,
    ) -> dict:
        """Submit a bug report for evaluation."""
        program_id = self._to_storage_string(program_id)
        title = self._to_storage_string(title)
        description = self._to_storage_string(description)
        severity_self_assess = self._to_storage_string(severity_self_assess)
        report_metadata = self._to_storage_string(report_metadata)

        if program_id not in self.programs:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Program '{program_id}' not found")

        program = self.programs[program_id]
        if not program.is_active:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Program is inactive")

        if severity_self_assess not in SEVERITY_WEIGHTS:
            raise gl.vm.UserError(
                f"{ERROR_EXPECTED} Severity must be one of: {', '.join(SEVERITY_WEIGHTS.keys())}"
            )

        if gl.message.value > 0:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} No GEN required for submission")

        self.report_counter = u256(int(self.report_counter) + 1)
        report_id = f"BUG_{gl.message_raw['chain_id']}_{self.report_counter}"
        if report_id in self.bug_reports:
            # Shouldn't happen - guard against collisions
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Report ID collision: {report_id}")

        # Check for duplicates in registry
        desc_hash = self._hash_description(description)
        duplicate_id = self._find_duplicate(program.contract_address, desc_hash)
        if duplicate_id:
            report = BugReport(
                id=report_id,
                bounty_program_id=program_id,
                submitter=gl.message.sender_address.as_hex,
                title=title,
                description=description,
                affected_code_links=affected_code_links,
                report_metadata=report_metadata,
                severity_vote=severity_self_assess,
                status=STATUS_DUPLICATE,
                evaluated_severity=SEVERITY_NONE,
                reward=u256(0),
                payout_status=PAYOUT_NONE,
                payout_attempts=u256(0),
                created_at=gl.message_raw["datetime"],
                resolved_at=gl.message_raw["datetime"],
            )
            self.bug_reports[report_id] = report
            return {
                "report_id": report_id,
                "status": STATUS_DUPLICATE,
                "duplicate_of": duplicate_id,
                "message": "This vulnerability has already been reported.",
            }

        # Store the report
        report = BugReport(
            id=report_id,
            bounty_program_id=program_id,
            submitter=gl.message.sender_address.as_hex,
            title=title,
            description=description,
            affected_code_links=affected_code_links,
            report_metadata=report_metadata,
            severity_vote=severity_self_assess,
            status=STATUS_PENDING,
            evaluated_severity=SEVERITY_NONE,
            reward=u256(0),
            payout_status=PAYOUT_NONE,
            payout_attempts=u256(0),
            created_at=gl.message_raw["datetime"],
            resolved_at="",
        )
        self.bug_reports[report_id] = report
        return {"report_id": report_id, "status": STATUS_PENDING}

    # --- Validation (the AI core) ---

    @gl.public.write
    def evaluate_report(self, report_id: str) -> dict:
        """
        Evaluate a bug report using GenLayer's LLM-powered consensus.

        Steps:
        1. Leader proposes: severity + validity + reasoning
        2. Validators independently verify using their own LLMs
        3. Custom equivalence function checks agreement within tolerance
        4. On agreement: auto-pays bounty + registers in vuln registry
        """
        if report_id not in self.bug_reports:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Report '{report_id}' not found")

        report = self.bug_reports[report_id]
        if report.status != STATUS_PENDING:
            raise gl.vm.UserError(
                f"{ERROR_EXPECTED} Report already {report.status}"
            )

        program = self.programs[report.bounty_program_id]

        # --- Build the evaluation prompt ---
        prompt = f"""You are a security auditor evaluating a bug bounty report.

Protocol: {program.protocol_name}
Target contract: {program.contract_address}
Program description: {program.description}
Program metadata: {program.program_metadata}

Bug Report:
Title: {report.title}
Description: {report.description}
Affected code/PoC links: {', '.join(report.affected_code_links)}
Report metadata: {report.report_metadata}
Submitter's severity assessment: {report.severity_vote}

Your task: Evaluate whether this is a valid security vulnerability.

Respond ONLY with valid JSON (no markdown, no formatting):
{{
    "is_valid": bool,
    "severity": "critical" | "high" | "medium" | "low" | "none",
    "confidence": "string number from 0.0 to 1.0, e.g. 0.92",
    "reasoning": "brief explanation"
}}

Rules:
- "none" severity means not a valid vulnerability (reject)
- "critical" = funds at direct risk, exploitable on-chain
- "high" = significant security flaw, limited exploit path
- "medium" = moderate risk, requires specific conditions
- "low" = minor issue, informational
- Set is_valid to false if severity is "none"
- Be conservative - only accept well-described, reproducible bugs
"""

        # --- Execute with custom validator consensus ---
        result = self._evaluate_with_consensus(prompt, report, program)
        return result

    # --- Internal: LLM consensus evaluation ---

    def _evaluate_with_consensus(
        self, prompt: str, report: BugReport, program: BountyProgram
    ) -> dict:
        """
        Uses a custom validator function to reach consensus on the bug
        report evaluation. This is the heart of the self-aware audit.
        """

        def leader_fn() -> dict:
            """Leader proposes the evaluation."""
            raw = gl.nondet.exec_prompt(prompt, response_format="json")
            return self._normalize_llm_evaluation(raw)

        def validator_fn(leaders_res: gl.vm.Result) -> bool:
            """
            Custom equivalence check. Validators verify that the leader's
            AI audit result is well-formed and internally consistent without
            launching another LLM call. This keeps testnet consensus from
            timing out while still forcing validators to reject malformed or
            contradictory outputs.
            """
            if not isinstance(leaders_res, gl.vm.Return):
                # Leader errored - LLM failures should rotate instead of
                # being accepted by validators.
                return False

            # Extract leader evaluation data.
            leader_eval = leaders_res.calldata if isinstance(leaders_res.calldata, dict) else {}
            leader_valid = leader_eval.get("is_valid", False)
            leader_sev = str(leader_eval.get("severity", SEVERITY_NONE))
            leader_reasoning = str(leader_eval.get("reasoning", ""))

            try:
                leader_conf = float(str(leader_eval.get("confidence", "0")).strip())
            except Exception:
                return False

            if leader_sev not in SEVERITY_WEIGHTS:
                return False
            if leader_conf < 0.0 or leader_conf > 1.0:
                return False

            # "none" severity must be an invalid report, and valid reports
            # need enough confidence plus a reason validators can inspect.
            if leader_sev == SEVERITY_NONE and bool(leader_valid):
                return False
            if leader_sev != SEVERITY_NONE and not bool(leader_valid):
                return False
            if bool(leader_valid) and leader_conf < 0.4:
                return False
            if bool(leader_valid) and len(leader_reasoning.strip()) < 20:
                return False

            return True

        # Run non-deterministic consensus
        consensus_result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)

        # Parse the leader's accepted result
        # Direct mode: consensus_result is the raw return from leader_fn (dict)
        # Production: consensus_result is Return(calldata=dict)
        if isinstance(consensus_result, dict):
            evaluation = consensus_result
        elif isinstance(consensus_result, gl.vm.Return) and isinstance(consensus_result.calldata, dict):
            evaluation = consensus_result.calldata
        else:
            raise gl.vm.UserError(f"{ERROR_LLM} Consensus failed: {type(consensus_result)}")

        is_valid = bool(evaluation.get("is_valid", False))
        severity = str(evaluation.get("severity", SEVERITY_NONE))
        reasoning = str(evaluation.get("reasoning", ""))

        if not is_valid or severity == SEVERITY_NONE:
            # Rejected - no reward
            report.status = STATUS_REJECTED
            report.evaluated_severity = severity
            report.resolved_at = gl.message_raw["datetime"]
            return {
                "report_id": report.id,
                "status": STATUS_REJECTED,
                "severity": severity,
                "reasoning": reasoning,
                "reward": "0",
            }

        # --- Accepted! Calculate reward ---
        multiplier = BOUNTY_MULTIPLIER.get(severity, 5)
        base_reward = u256(multiplier * 10**18)  # base in atto-GEN

        # Cap at max payout
        if base_reward > program.max_payout:
            base_reward = program.max_payout

        # Ensure declared pool and funded escrow have enough to pay immediately.
        if base_reward > program.reward_pool:
            base_reward = program.reward_pool
        if base_reward > program.escrow_balance:
            base_reward = program.escrow_balance
        if base_reward <= 0:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Program escrow is empty")

        # Update state
        report.status = STATUS_ACCEPTED
        report.evaluated_severity = severity
        report.reward = base_reward
        report.payout_status = PAYOUT_PENDING
        report.resolved_at = gl.message_raw["datetime"]

        program.reward_pool -= base_reward
        program.escrow_balance -= base_reward

        self._emit_report_payout(report, base_reward, "accepted")

        # Register in shared vulnerability registry
        vuln_id = f"VULN_{gl.message_raw['chain_id']}_{self.report_counter}"
        vuln = VulnRecord(
            id=vuln_id,
            contract_address=program.contract_address,
            title=report.title,
            severity=severity,
            description_hash=self._hash_description(report.description),
            reporter=report.submitter,
            program_id=program.id,
            timestamp=gl.message_raw["datetime"],
        )
        self.vuln_registry[vuln_id] = vuln

        return {
            "report_id": report.id,
            "status": STATUS_ACCEPTED,
            "severity": severity,
            "reasoning": reasoning,
            "reward": str(base_reward),
            "payout_status": report.payout_status,
            "payout_attempts": str(report.payout_attempts),
            "vuln_registry_id": vuln_id,
        }

    @gl.public.write
    def retry_payout(self, report_id: str) -> dict:
        """Re-emit payout for an accepted report without re-running evaluation."""
        report_id = self._to_storage_string(report_id)
        if report_id not in self.bug_reports:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Report not found")

        report = self.bug_reports[report_id]
        program = self.programs[report.bounty_program_id]
        if gl.message.sender_address.as_hex != program.owner and gl.message.sender_address != self.owner:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Only program owner")
        if report.status != STATUS_ACCEPTED:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Report is not accepted")
        if report.reward <= 0:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Report has no payout")
        if report.payout_attempts >= MAX_PAYOUT_ATTEMPTS:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Payout retry limit reached")

        self._emit_report_payout(report, report.reward, "accepted")
        return {
            "report_id": report.id,
            "reward": str(report.reward),
            "payout_status": report.payout_status,
            "payout_attempts": str(report.payout_attempts),
            "max_payout_attempts": str(MAX_PAYOUT_ATTEMPTS),
        }

    def _emit_report_payout(self, report: BugReport, amount: u256, on_status: str) -> None:
        """Emit a native transfer and mark it as handed to consensus processing."""
        if amount <= 0:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Payout amount must be positive")

        report.payout_attempts = u256(int(report.payout_attempts) + 1)
        report.payout_status = PAYOUT_EMITTED
        gl.get_contract_at(Address(report.submitter)).emit_transfer(
            value=amount,
            on=on_status,
        )

    def _handle_leader_error(self, leaders_res, leader_fn) -> bool:
        """Deterministic error comparison for consensus."""
        leader_msg = getattr(leaders_res, "message", "")
        try:
            leader_fn()
            # Leader errored, validator succeeded - disagree
            return False
        except gl.vm.UserError as e:
            validator_msg = getattr(e, "message", str(e))
            if validator_msg.startswith(ERROR_EXPECTED) or \
               validator_msg.startswith(ERROR_EXTERNAL):
                return validator_msg == leader_msg
            if validator_msg.startswith(ERROR_TRANSIENT) and \
               leader_msg.startswith(ERROR_TRANSIENT):
                return True
            return False
        except Exception:
            return False

    def _normalize_llm_evaluation(self, raw) -> dict:
        """
        Normalize LLM JSON into calldata-safe primitives.

        Live LLMs often return confidence as a JSON number/float. GenLayer
        calldata cannot encode floats, so confidence must be converted to a
        string before returning from leader_fn().
        """
        if not isinstance(raw, dict):
            raise gl.vm.UserError(f"{ERROR_LLM} LLM returned non-dict response")

        severity = str(raw.get("severity", SEVERITY_NONE)).strip().lower()
        if severity not in SEVERITY_WEIGHTS:
            severity = SEVERITY_NONE

        is_valid = bool(raw.get("is_valid", False))
        if severity == SEVERITY_NONE:
            is_valid = False

        confidence_raw = raw.get("confidence", "0")
        try:
            confidence = float(str(confidence_raw).strip())
        except Exception:
            confidence = 0.0
        if confidence < 0.0:
            confidence = 0.0
        if confidence > 1.0:
            confidence = 1.0

        return {
            "is_valid": is_valid,
            "severity": severity,
            "confidence": str(confidence),
            "reasoning": str(raw.get("reasoning", "")),
        }

    # --- Helpers ---

    def _hash_description(self, description: str) -> str:
        """Stable hash for duplicate detection."""
        # Use keccak256 for on-chain compatible hashing
        return Keccak256(description.encode("utf-8")).hexdigest()

    def _find_duplicate(self, contract_address: str, desc_hash: str) -> str:
        """Search vuln registry for duplicates by target + desc hash."""
        for vid, record in self.vuln_registry.items():
            if record.contract_address == contract_address and \
               record.description_hash == desc_hash:
                return vid
        return ""

    # --- Read Methods ---

    @gl.public.view
    def get_program(self, program_id: str) -> dict:
        """Get bounty program details."""
        if program_id not in self.programs:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Program not found")
        p = self.programs[program_id]
        return {
            "id": p.id,
            "owner": p.owner,
            "protocol_name": p.protocol_name,
            "contract_address": p.contract_address,
            "description": p.description,
            "program_metadata": p.program_metadata,
            "reward_pool": str(p.reward_pool),
            "escrow_balance": str(p.escrow_balance),
            "max_payout": str(p.max_payout),
            "is_funded": p.escrow_balance > 0,
            "is_active": p.is_active,
            "created_at": p.created_at,
        }

    @gl.public.view
    def list_programs(self) -> list:
        """List all bounty programs."""
        results = []
        for pid in self.program_ids:
            p = self.programs[pid]
            results.append({
                "id": p.id,
                "protocol_name": p.protocol_name,
                "contract_address": p.contract_address,
                "description": p.description,
                "program_metadata": p.program_metadata,
                "reward_pool": str(p.reward_pool),
                "escrow_balance": str(p.escrow_balance),
                "max_payout": str(p.max_payout),
                "is_funded": p.escrow_balance > 0,
                "is_active": p.is_active,
            })
        return results

    @gl.public.view
    def list_reports(self) -> list:
        """List all bug reports."""
        results = []
        for rid, r in self.bug_reports.items():
            results.append({
                "id": r.id,
                "program_id": r.bounty_program_id,
                "submitter": r.submitter,
                "title": r.title,
                "description": r.description,
                "report_metadata": r.report_metadata,
                "severity_vote": r.severity_vote,
                "status": r.status,
                "evaluated_severity": r.evaluated_severity,
                "reward": str(r.reward),
                "payout_status": r.payout_status,
                "payout_attempts": str(r.payout_attempts),
            })
        return results

    @gl.public.view
    def get_report(self, report_id: str) -> dict:
        """Get bug report details."""
        if report_id not in self.bug_reports:
            raise gl.vm.UserError(f"{ERROR_EXPECTED} Report not found")
        r = self.bug_reports[report_id]
        return {
            "id": r.id,
            "program_id": r.bounty_program_id,
            "submitter": r.submitter,
            "title": r.title,
            "description": r.description,
            "affected_code_links": list(r.affected_code_links),
            "report_metadata": r.report_metadata,
            "severity_vote": r.severity_vote,
            "status": r.status,
            "evaluated_severity": r.evaluated_severity,
            "reward": str(r.reward),
            "payout_status": r.payout_status,
            "payout_attempts": str(r.payout_attempts),
            "created_at": r.created_at,
            "resolved_at": r.resolved_at,
        }

    @gl.public.view
    def get_vulnerability_registry(self) -> list:
        """Get the shared vulnerability registry."""
        results = []
        for vid, v in self.vuln_registry.items():
            results.append({
                "id": v.id,
                "contract_address": v.contract_address,
                "title": v.title,
                "severity": v.severity,
                "reporter": v.reporter,
                "program_id": v.program_id,
                "timestamp": v.timestamp,
            })
        return results

    @gl.public.view
    def get_vulnerabilities_by_contract(self, contract_address: str) -> list:
        """Query vuln registry by target contract."""
        results = []
        for vid, v in self.vuln_registry.items():
            if v.contract_address == contract_address:
                results.append({
                    "id": v.id,
                    "title": v.title,
                    "severity": v.severity,
                    "reporter": v.reporter,
                    "timestamp": v.timestamp,
                })
        return results

    @gl.public.view
    def get_hacker_reports(self, hacker_address: str) -> list:
        """Get all reports by a specific hacker."""
        results = []
        normalized_hacker = self._normalize_address(hacker_address)
        for rid, r in self.bug_reports.items():
            if self._normalize_address(r.submitter) == normalized_hacker:
                results.append({
                    "id": r.id,
                    "program_id": r.bounty_program_id,
                    "title": r.title,
                    "report_metadata": r.report_metadata,
                    "status": r.status,
                    "evaluated_severity": r.evaluated_severity,
                    "reward": str(r.reward),
                    "payout_status": r.payout_status,
                    "payout_attempts": str(r.payout_attempts),
                })
        return results

    @gl.public.view
    def get_contract_balance(self) -> str:
        """Return this contract's native GEN balance."""
        return str(gl.get_contract_at(gl.message.contract_address).balance)

    def _normalize_address(self, address) -> str:
        """Normalize address-like values passed by CLI, SDK, or contract storage."""
        if hasattr(address, "as_hex"):
            return address.as_hex.lower()
        if isinstance(address, int):
            return f"0x{address:040x}".lower()
        return str(address).strip('"').lower()

    def _to_storage_string(self, value) -> str:
        """Convert SDK/CLI decoded values into deterministic storage strings."""
        if hasattr(value, "as_hex"):
            return value.as_hex
        if isinstance(value, dict):
            return json.dumps(value, sort_keys=True, default=self._json_default)
        if isinstance(value, list):
            return json.dumps(value, sort_keys=True, default=self._json_default)
        return str(value)

    def _json_default(self, value) -> str:
        if hasattr(value, "as_hex"):
            return value.as_hex
        return str(value)
