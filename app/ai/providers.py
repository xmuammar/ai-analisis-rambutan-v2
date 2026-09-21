from abc import ABC, abstractmethod

from app.ai.types import InspectionInputs, Prediction


class AIProvider(ABC):
    name = "abstract"

    @abstractmethod
    def analyze(self, inputs: InspectionInputs) -> tuple[Prediction, ...]:
        raise NotImplementedError


class LocalAIProvider(AIProvider):
    name = "local-rules"

    def analyze(self, inputs: InspectionInputs) -> tuple[Prediction, ...]:
        from app.ai.soil import infer_virtual_soil

        return (infer_virtual_soil(inputs),)


class RemoteAIProvider(AIProvider):
    name = "remote-unavailable"

    def analyze(self, inputs: InspectionInputs) -> tuple[Prediction, ...]:
        return ()


class AIProviderRouter:
    def __init__(self, local: AIProvider | None = None):
        self.local = local or LocalAIProvider()

    def analyze(self, inputs: InspectionInputs) -> tuple[Prediction, ...]:
        return self.local.analyze(inputs)
