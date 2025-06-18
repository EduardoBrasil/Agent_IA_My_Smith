from abc import ABC, abstractmethod

class AdaptationStrategy(ABC):
    @abstractmethod
    async def adapt(self, texto: str) -> str:
        pass
