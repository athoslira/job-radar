
from abc import ABC, abstractmethod

from core.job import Job


class FonteIndisponivel(RuntimeError):
    """A fonte não conseguiu concluir nenhuma das consultas planejadas."""


class BaseScraper(ABC):

    def _executar_consulta(self, consulta, *args, **kwargs) -> list[Job]:
        """Executa uma consulta isolada e preserva falhas parciais.

        Portais que fazem várias buscas por termo/local não devem perder os
        resultados já coletados porque uma única consulta falhou. Ao mesmo
        tempo, o orquestrador precisa saber se a fonte falhou por completo ou
        parcialmente para decidir se deve repeti-la no próximo ciclo.
        """
        self._consultas_total = getattr(self, "_consultas_total", 0) + 1
        try:
            resultado = consulta(*args, **kwargs)
        except FonteIndisponivel:
            self._consultas_com_falha = getattr(self, "_consultas_com_falha", 0) + 1
            return []

        self._consultas_com_sucesso = getattr(self, "_consultas_com_sucesso", 0) + 1
        return resultado

    def _validar_disponibilidade(self) -> None:
        total = getattr(self, "_consultas_total", 0)
        sucessos = getattr(self, "_consultas_com_sucesso", 0)
        falhas = getattr(self, "_consultas_com_falha", 0)
        if total and sucessos == 0 and falhas:
            raise FonteIndisponivel(
                f"todas as {total} consulta(s) da fonte falharam"
            )

    @property
    def consultas_com_falha(self) -> int:
        return getattr(self, "_consultas_com_falha", 0)

    @property
    def consultas_total(self) -> int:
        return getattr(self, "_consultas_total", 0)

    @abstractmethod
    def buscar_vagas(self) -> list[Job]:
        pass
