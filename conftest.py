import os
from pathlib import Path
from typing import Any, Optional

import pytest
from gltest.direct.loader import deploy_contract


@pytest.fixture
def direct_deploy(direct_vm):
    """Deploy contracts with the GenVM SDK version used by local validation."""

    def _deploy(contract_path: str, *args: Any, sdk_version: Optional[str] = None, **kwargs: Any) -> Any:
        path = Path(contract_path)
        if not path.is_absolute():
            for base in (Path.cwd(), Path.cwd() / "contracts", Path.cwd() / "intelligent-contracts"):
                candidate = base / contract_path
                if candidate.exists():
                    path = candidate.resolve()
                    break

        version = sdk_version or os.environ.get("GENVM_VERSION", "v0.2.16")
        return deploy_contract(path, direct_vm, *args, sdk_version=version, **kwargs)

    return _deploy
