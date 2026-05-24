"""Direct-mode tests for the SecurityBounty intelligent contract.

Tests run fast (~30-50ms) using mock VM — no server, no Docker needed.
Mocks web requests and LLM responses to test contract logic in isolation.
"""

import json
import pytest

# Contract path relative to project root
CONTRACT_PATH = "contracts/security_bounty.py"


# ──────────────────────────────────────────────────────────────
# Fixtures & Helpers
# ──────────────────────────────────────────────────────────────

PROGRAM_ID = "testdefi_1"


def _make_eval_response(is_valid=True, severity="high", confidence="0.85", reasoning="Found reentrancy"):
    return json.dumps({
        "is_valid": is_valid,
        "severity": severity,
        "confidence": confidence,
        "reasoning": reasoning,
    })


def install_native_transfer_hook(direct_vm):
    """Apply emitted native transfers to direct-mode balances."""
    if getattr(direct_vm, "_security_bounty_transfer_hook", False):
        return

    def hook(vm, request):
        if "EthSend" in request:
            transfer = request["EthSend"]
        elif "PostMessage" in request:
            transfer = request["PostMessage"]
        else:
            return None

        value = int(transfer.get("value", 0))
        if value <= 0:
            return {"ok": None}

        contract_addr = vm._to_bytes(vm._contract_address)
        recipient = vm._to_bytes(transfer["address"])
        contract_balance = vm._balances.get(contract_addr, 0)
        if contract_balance < value:
            raise RuntimeError("insufficient direct-mode contract balance")

        vm._balances[contract_addr] = contract_balance - value
        vm._balances[recipient] = vm._balances.get(recipient, 0) + value
        return {"ok": None}

    direct_vm._gl_call_hook = hook
    direct_vm._security_bounty_transfer_hook = True


def _fund_contract_balance(direct_vm, amount):
    contract_addr = direct_vm._to_bytes(direct_vm._contract_address)
    direct_vm.deal(contract_addr, direct_vm._balances.get(contract_addr, 0) + amount)


def create_program(
    contract,
    name="TestDeFi",
    target="0x1234",
    desc="desc",
    pool=1000,
    max_payout=100,
    direct_vm=None,
    escrow=0,
):
    previous_value = None
    if direct_vm is not None:
        previous_value = direct_vm.value
        direct_vm.value = escrow
        if escrow > 0:
            _fund_contract_balance(direct_vm, escrow)

    try:
        return contract.create_program(
            name,
            target,
            desc,
            pool,
            max_payout,
            json.dumps({
                "brief": "",
                "inScope": target,
                "outOfScope": "",
                "rules": "",
                "safeHarbor": "",
                "disclosurePolicy": "",
                "rewardTable": "",
            }),
        )
    finally:
        if direct_vm is not None:
            direct_vm.value = previous_value


def submit_report(contract, program_id=PROGRAM_ID, title="Bug", desc="desc", links=None, severity="high"):
    return contract.submit_report(
        program_id,
        title,
        desc,
        links or ["link"],
        severity,
        json.dumps({
            "affectedTarget": "0x1234",
            "category": "access control",
            "impact": "An attacker can cause security impact.",
            "steps": "1. Prepare exploit\n2. Execute exploit",
            "proof": "PoC",
            "remediation": "",
        }),
    )


# ──────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────

def test_create_program(direct_vm, direct_deploy, direct_owner):
    """Should create a bounty program with correct initial state."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner

    result = create_program(
        contract,
        desc="Bug bounty for TestDeFi protocol",
        pool=1000000,
        max_payout=50000,
    )

    assert result["program_id"] == PROGRAM_ID
    assert result["reward_pool"] == "1000000"
    assert result["escrow_balance"] == "0"
    assert result["is_funded"] is False

    # Read it back
    prog = contract.get_program(PROGRAM_ID)
    assert prog["protocol_name"] == "TestDeFi"
    assert prog["contract_address"] == "0x1234"
    assert prog["is_active"] is True
    assert prog["reward_pool"] == "1000000"
    assert prog["escrow_balance"] == "0"
    assert prog["max_payout"] == "50000"


def test_create_funded_program(direct_vm, direct_deploy, direct_owner):
    """Program creation can escrow native GEN for automatic payouts."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner

    result = create_program(
        contract,
        pool=1000000,
        max_payout=50000,
        direct_vm=direct_vm,
        escrow=1000000,
    )

    assert result["escrow_balance"] == "1000000"
    assert result["is_funded"] is True
    assert contract.get_program(PROGRAM_ID)["escrow_balance"] == "1000000"


def test_fund_program(direct_vm, direct_deploy, direct_owner, direct_alice):
    """Program owners can top up escrow after creation."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner
    create_program(contract, pool=1000, max_payout=100)

    previous_value = direct_vm.value
    direct_vm.value = 500
    _fund_contract_balance(direct_vm, 500)
    result = contract.fund_program(PROGRAM_ID)
    direct_vm.value = previous_value

    assert result["reward_pool"] == "1000"
    assert result["escrow_balance"] == "500"

    direct_vm.sender = direct_alice
    direct_vm.value = 1
    with direct_vm.expect_revert("Only program owner"):
        contract.fund_program(PROGRAM_ID)
    direct_vm.value = 0


def test_create_program_by_non_deployer(direct_vm, direct_deploy, direct_alice):
    """Any caller should be able to create and own a bounty program."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_alice

    result = create_program(contract)

    assert result["program_id"] == PROGRAM_ID
    prog = contract.get_program(PROGRAM_ID)
    assert prog["owner"].casefold() == ("0x" + direct_alice.hex()).casefold()


def test_create_program_with_bounty_brief(direct_vm, direct_deploy, direct_owner):
    """Program briefs should persist scope, policy, and reward metadata."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner

    contract.create_program(
        "TestDeFi",
        "0x1234",
        "desc",
        1000,
        100,
        json.dumps({
            "brief": "Focus on vault and router contracts",
            "inScope": "0x1234\n0xabcd",
            "outOfScope": "DoS, social engineering",
            "rules": "No destructive testing",
            "safeHarbor": "Good-faith research is authorized",
            "disclosurePolicy": "Ask permission before public disclosure",
            "rewardTable": "critical: 100\nhigh: 50",
        }),
    )

    prog = contract.get_program(PROGRAM_ID)
    meta = json.loads(prog["program_metadata"])
    assert meta["brief"] == "Focus on vault and router contracts"
    assert "0xabcd" in meta["inScope"]
    assert "social engineering" in meta["outOfScope"]
    assert meta["safeHarbor"] == "Good-faith research is authorized"
    assert "critical" in meta["rewardTable"]


def test_create_duplicate_program(direct_vm, direct_deploy, direct_owner):
    """Creating a program with the same ID should fail."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner

    create_program(contract)
    with direct_vm.expect_revert("already exists"):
        create_program(contract)


def test_deactivate_program(direct_vm, direct_deploy, direct_owner):
    """Should deactivate an active program."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner

    create_program(contract)
    result = contract.deactivate_program(PROGRAM_ID)

    assert result["status"] == "deactivated"
    prog = contract.get_program(PROGRAM_ID)
    assert prog["is_active"] is False


def test_deactivate_program_not_program_owner(direct_vm, direct_deploy, direct_owner, direct_alice):
    """Should reject deactivation by anyone except the program owner."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner
    create_program(contract)

    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("Only program owner"):
        contract.deactivate_program(PROGRAM_ID)


def test_submit_report(direct_vm, direct_deploy, direct_owner, direct_alice):
    """Hacker should be able to submit a bug report."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner
    create_program(contract, desc="Bug bounty desc", pool=1000000, max_payout=50000)

    direct_vm.sender = direct_alice
    result = submit_report(
        contract,
        title="Reentrancy vulnerability in withdraw()",
        desc="The withdraw() function calls _send() before updating the balance, allowing reentrant calls to drain funds.",
        links=["https://github.com/testdefi/contracts/blob/main/withdraw.sol#L42"],
    )

    assert result["status"] == "pending"
    assert "report_id" in result

    # Check report is stored
    report = contract.get_report(result["report_id"])
    assert report["title"] == "Reentrancy vulnerability in withdraw()"
    assert report["submitter"].casefold() == ("0x" + direct_alice.hex()).casefold()
    assert report["status"] == "pending"


def test_submit_structured_report_metadata(direct_vm, direct_deploy, direct_owner, direct_alice):
    """Structured report fields should be stored for triage and AI evaluation."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner
    create_program(contract, desc="Bug bounty desc", pool=1000000, max_payout=50000)

    direct_vm.sender = direct_alice
    result = contract.submit_report(
        PROGRAM_ID,
        "Oracle manipulation",
        "The price oracle can be moved inside the same transaction.",
        ["https://github.com/testdefi/contracts/blob/main/oracle.sol#L9"],
        "critical",
        json.dumps({
            "affectedTarget": "0x1234:Oracle",
            "category": "oracle manipulation",
            "impact": "An attacker can drain undercollateralized loans.",
            "steps": "1. Flash borrow\n2. Move price\n3. Borrow against bad price",
            "proof": "forge test --match-test testOracleManipulation",
            "remediation": "Use TWAP and sanity bounds.",
        }),
    )

    report = contract.get_report(result["report_id"])
    meta = json.loads(report["report_metadata"])
    assert meta["affectedTarget"] == "0x1234:Oracle"
    assert meta["category"] == "oracle manipulation"
    assert "drain" in meta["impact"]
    assert "Flash borrow" in meta["steps"]
    assert "forge test" in meta["proof"]
    assert "TWAP" in meta["remediation"]


def test_submit_report_inactive_program(direct_vm, direct_deploy, direct_owner, direct_alice):
    """Should reject submissions to inactive programs."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner
    create_program(contract)
    contract.deactivate_program(PROGRAM_ID)

    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("inactive"):
        submit_report(contract)


def test_submit_report_invalid_severity(direct_vm, direct_deploy, direct_owner, direct_alice):
    """Should reject invalid severity values."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner
    create_program(contract)

    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("Severity"):
        submit_report(contract, severity="extreme")


def test_evaluate_valid_bug(direct_vm, direct_deploy, direct_owner, direct_alice):
    """Evaluate a valid bug report — should accept and pay reward."""
    contract = direct_deploy(CONTRACT_PATH)
    install_native_transfer_hook(direct_vm)
    direct_vm.sender = direct_owner
    create_program(
        contract,
        desc="Critical bug bounty for TestDeFi protocol",
        pool=1000000,
        max_payout=50000,
        direct_vm=direct_vm,
        escrow=1000000,
    )

    direct_vm.sender = direct_alice
    submit_result = submit_report(
        contract,
        title="Reentrancy in withdraw()",
        desc="The withdraw() function sends ETH before updating balance, allowing reentrancy.",
        links=["https://github.com/testdefi/contracts/blob/main/withdraw.sol#L42"],
        severity="critical",
    )
    report_id = submit_result["report_id"]

    # Mock the LLM evaluation to return a valid high-severity result
    direct_vm.mock_llm(
            r".*security auditor evaluating.*",
            _make_eval_response(is_valid=True, severity="high", confidence="0.92", reasoning="Valid reentrancy vulnerability"),
        )

    direct_vm.sender = direct_owner
    alice_before = direct_vm._balances.get(direct_vm._to_bytes(direct_alice), 0)
    result = contract.evaluate_report(report_id)

    assert result["status"] == "accepted"
    assert result["severity"] == "high"
    # high severity = 50 * 10^18 atto-GEN
    assert result["reward"] == "50000"
    assert result["payout_status"] == "emitted"
    assert "vuln_registry_id" in result
    assert direct_vm._balances.get(direct_vm._to_bytes(direct_alice), 0) == alice_before + 50000

    # Check state
    report = contract.get_report(report_id)
    assert report["status"] == "accepted"
    assert report["evaluated_severity"] == "high"
    assert contract.get_program(PROGRAM_ID)["escrow_balance"] == "950000"


def test_retry_payout_reemits_transfer(direct_vm, direct_deploy, direct_owner, direct_alice):
    """Accepted reports can re-emit payout without a second AI evaluation."""
    contract = direct_deploy(CONTRACT_PATH)
    install_native_transfer_hook(direct_vm)
    direct_vm.sender = direct_owner
    create_program(
        contract,
        pool=1000000,
        max_payout=50000,
        direct_vm=direct_vm,
        escrow=1000000,
    )

    direct_vm.sender = direct_alice
    submit_result = submit_report(
        contract,
        title="Reentrancy in withdraw()",
        desc="The withdraw() function sends ETH before updating balance, allowing reentrancy.",
        severity="high",
    )
    report_id = submit_result["report_id"]

    direct_vm.mock_llm(
        r".*security auditor evaluating.*",
        _make_eval_response(is_valid=True, severity="high", confidence="0.92", reasoning="Valid reentrancy vulnerability"),
    )

    direct_vm.sender = direct_owner
    contract.evaluate_report(report_id)

    alice_after_eval = direct_vm._balances.get(direct_vm._to_bytes(direct_alice), 0)
    result = contract.retry_payout(report_id)

    assert result["payout_status"] == "emitted"
    assert result["payout_attempts"] == "2"
    assert direct_vm._balances.get(direct_vm._to_bytes(direct_alice), 0) == alice_after_eval + 50000


def test_normalize_llm_numeric_confidence(direct_deploy):
    """Contract normalizer converts live LLM numeric confidence to calldata-safe string."""
    contract = direct_deploy(CONTRACT_PATH)

    normalized = contract._normalize_llm_evaluation({
        "is_valid": True,
        "severity": "medium",
        "confidence": 0.87,
        "reasoning": "Valid medium severity issue",
    })

    assert normalized["is_valid"] is True
    assert normalized["severity"] == "medium"
    assert normalized["confidence"] == "0.87"
    assert normalized["reasoning"] == "Valid medium severity issue"


def test_evaluate_invalid_bug(direct_vm, direct_deploy, direct_owner, direct_alice):
    """Evaluate an invalid bug report — should reject."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner
    create_program(contract, pool=1000000, max_payout=50000)

    direct_vm.sender = direct_alice
    submit_result = submit_report(
        contract,
        title="Fake bug",
        desc="I think there might be a bug somewhere but I'm not sure",
        links=["https://github.com/testdefi/contracts/blob/main/main.sol"],
        severity="low",
    )
    report_id = submit_result["report_id"]

    direct_vm.mock_llm(
        r".*security auditor evaluating.*",
        _make_eval_response(is_valid=False, severity="none", confidence="0.95", reasoning="Not a valid vulnerability"),
    )

    direct_vm.sender = direct_owner
    result = contract.evaluate_report(report_id)

    assert result["status"] == "rejected"
    assert result["severity"] == "none"
    assert result["reward"] == "0"


def test_evaluate_twice(direct_vm, direct_deploy, direct_owner, direct_alice):
    """Should not allow re-evaluating an already-evaluated report."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner
    create_program(contract, pool=1000000, max_payout=50000)

    direct_vm.sender = direct_alice
    submit_result = submit_report(contract)
    report_id = submit_result["report_id"]

    direct_vm.mock_llm(
        r".*security auditor evaluating.*",
        _make_eval_response(is_valid=False, severity="none", confidence="0.8", reasoning="Not valid"),
    )

    direct_vm.sender = direct_owner
    contract.evaluate_report(report_id)

    # Second evaluation should revert
    with direct_vm.expect_revert("already"):
        contract.evaluate_report(report_id)


def test_vuln_registry_query(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob):
    """Vulnerability registry should be queryable by contract address."""
    contract = direct_deploy(CONTRACT_PATH)
    install_native_transfer_hook(direct_vm)
    direct_vm.sender = direct_owner
    create_program(contract, pool=1000000, max_payout=50000, direct_vm=direct_vm, escrow=1000000)

    # Submit and accept a bug
    direct_vm.sender = direct_alice
    sub1 = submit_report(contract, title="Bug A", desc="desc A", links=["link1"])
    direct_vm.mock_llm(
        r".*security auditor evaluating.*",
        _make_eval_response(is_valid=True, severity="high", confidence="0.9", reasoning="Valid"),
    )
    direct_vm.sender = direct_owner
    contract.evaluate_report(sub1["report_id"])

    # Query the registry
    vulns = contract.get_vulnerabilities_by_contract("0x1234")
    assert len(vulns) == 1
    assert vulns[0]["title"] == "Bug A"
    assert vulns[0]["severity"] == "high"

    # All registry
    all_vulns = contract.get_vulnerability_registry()
    assert len(all_vulns) == 1


def test_hacker_reports_query(direct_vm, direct_deploy, direct_owner, direct_alice, direct_bob):
    """Should return all reports by a specific hacker."""
    contract = direct_deploy(CONTRACT_PATH)
    direct_vm.sender = direct_owner
    create_program(contract, pool=1000000, max_payout=50000)

    direct_vm.sender = direct_alice
    submit_report(contract, title="Bug 1", desc="desc 1", links=["link1"])
    submit_report(contract, title="Bug 2", desc="desc 2", links=["link2"], severity="medium")

    # Build the addresses using Address type so hex format matches
    from genlayer.py.types import Address
    alice_addr = Address(direct_alice)
    reports = contract.get_hacker_reports(alice_addr.as_hex)
    assert len(reports) == 2
    assert all(r["title"] for r in reports)

    mixed_case_reports = contract.get_hacker_reports(alice_addr.as_hex.upper())
    assert len(mixed_case_reports) == 2

    address_object_reports = contract.get_hacker_reports(alice_addr)
    assert len(address_object_reports) == 2
