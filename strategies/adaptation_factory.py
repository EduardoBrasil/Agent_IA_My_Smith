from .comercial_strategy import ComercialStrategy
from .suporte_strategy import SuporteStrategy
from .produto_strategy import ProdutoStrategy

class AdaptationFactory:
    @staticmethod
    def get_strategy(audiencia: str):
        if audiencia == 'comercial':
            return ComercialStrategy()
        elif audiencia == 'suporte':
            return SuporteStrategy()
        elif audiencia == 'produto':
            return ProdutoStrategy()
        else:
            raise ValueError(f"Audiência desconhecida: {audiencia}")
