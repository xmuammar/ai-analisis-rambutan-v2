from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True)
class ModelManifest:
    model_id: str
    name: str
    task: str
    version: str
    runtime: str
    download_url: str | None = None
    checksum: str | None = None
    size_bytes: int | None = None
    minimum_app_version: str = "1.0.0"

    def verify(self, path: str | Path) -> bool:
        if not self.checksum:
            return False
        digest = sha256(Path(path).read_bytes()).hexdigest()
        return digest == self.checksum


class ModelManager:
    def __init__(self, model_directory: str | Path):
        self.model_directory = Path(model_directory)

    def installed(self, manifest: ModelManifest) -> bool:
        return any(
            candidate.exists()
            for candidate in (
                self.model_directory / manifest.model_id,
                self.model_directory / f"{manifest.model_id}.pt",
                self.model_directory / f"{manifest.model_id}.onnx",
            )
        )

    def status(self, manifest: ModelManifest) -> str:
        return "AVAILABLE" if self.installed(manifest) else "NOT_INSTALLED"
