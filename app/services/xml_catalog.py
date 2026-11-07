"""
Serviço de Leitura, Validação e Busca na Base XML de Imóveis.
Regras:
- Validar o arquivo antes de atualizar: se vier vazio ou com erro, manter a última
  versão válida em cache e registrar alerta para a Automação.
- Nunca oferecer imóvel vendido ou com disponibilidade zero.
- Respeitar o teto da cidade no MCMV 2026.
"""

import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from app.config import settings
from app.domain.mcmv import obter_regra_por_faixa_ou_renda, obter_teto_cidade, _normalizar_texto

logger = logging.getLogger("lili.xml_catalog")


@dataclass
class Imovel:
    codigo: str
    nome: str
    cidade: str
    bairro: str
    endereco: str
    tipo: str
    tipologia: str
    dormitorios: int
    suites: int
    vagas: int
    metragem_privativa: str
    valor_a_partir: float
    faixas_mcmv: list[str]
    status: str
    previsao_entrega: str
    disponibilidade: int
    diferencial: str
    foto: str
    link: str

    def formatar_apresentacao(self, observacao_proximidade: Optional[str] = None) -> dict:
        """
        Retorna os dados formatados segundo as regras obrigatórias da seção 7:
        - Sempre usar 'a partir de' e 'sujeito à disponibilidade'
        - Incluir nome, bairro, tipologia, metragem, valor 'a partir de',
          status de entrega, um diferencial, uma foto e o link da página no site.
        """
        valor_fmt = f"R$ {self.valor_a_partir:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        dados = {
            "codigo": self.codigo,
            "nome": self.nome,
            "cidade": self.cidade,
            "bairro": self.bairro,
            "tipo": self.tipo,
            "tipologia": self.tipologia,
            "dormitorios": self.dormitorios,
            "metragem_privativa": self.metragem_privativa,
            "valor_formatado": f"a partir de {valor_fmt} (sujeito à disponibilidade)",
            "valor_numerico": self.valor_a_partir,
            "status_entrega": f"{self.status} (Previsão: {self.previsao_entrega})",
            "disponibilidade": self.disponibilidade,
            "diferencial": self.diferencial,
            "foto": self.foto,
            "link": self.link,
        }
        if observacao_proximidade:
            dados["observacao_compatibilidade"] = observacao_proximidade
        return dados


class CatalogoImoveisXML:
    """Gerencia o cache validado da base XML e executa buscas com filtros."""

    def __init__(self, xml_path: Optional[Path] = None):
        self.xml_path: Path = xml_path or settings.XML_IMOVEIS_PATH
        self._imoveis_cache: list[Imovel] = []
        self._ultima_atualizacao_ts: float = 0.0
        self._alertas_automacao: list[str] = []
        self.recarregar_base(forcar=True)

    @property
    def alertas_automacao(self) -> list[str]:
        return list(self._alertas_automacao)

    def recarregar_base(self, forcar: bool = False, xml_content_override: Optional[str] = None) -> bool:
        """
        Lê e valida o XML. Se vier vazio ou com erro, mantém a última versão válida
        e registra alerta para a Automação.
        """
        agora = time.time()
        if (
            not forcar
            and xml_content_override is None
            and self._imoveis_cache
            and (agora - self._ultima_atualizacao_ts) < settings.XML_REFRESH_INTERVAL_SECONDS
        ):
            return True

        try:
            if xml_content_override is not None:
                conteudo = xml_content_override.strip()
            else:
                if not self.xml_path.exists():
                    raise FileNotFoundError(f"Arquivo XML não encontrado: {self.xml_path}")
                conteudo = self.xml_path.read_text(encoding="utf-8").strip()

            if not conteudo:
                raise ValueError("Arquivo XML está vazio.")

            root = ET.fromstring(conteudo)
            novos_imoveis: list[Imovel] = []

            for elem in root.findall("imovel"):
                codigo = (elem.findtext("codigo") or "").strip()
                nome = (elem.findtext("nome") or "").strip()
                cidade = (elem.findtext("cidade") or "").strip()
                valor_str = (elem.findtext("valor_a_partir") or "0").strip()
                disp_str = (elem.findtext("disponibilidade") or "0").strip()

                if not codigo or not nome or not cidade:
                    continue

                faixas_raw = elem.findtext("faixas_mcmv") or ""
                faixas = [f.strip() for f in faixas_raw.split(",") if f.strip()]

                imovel = Imovel(
                    codigo=codigo,
                    nome=nome,
                    cidade=cidade,
                    bairro=(elem.findtext("bairro") or "").strip(),
                    endereco=(elem.findtext("endereco") or "").strip(),
                    tipo=(elem.findtext("tipo") or "").strip(),
                    tipologia=(elem.findtext("tipologia") or "").strip(),
                    dormitorios=int(elem.findtext("dormitorios") or 0),
                    suites=int(elem.findtext("suites") or 0),
                    vagas=int(elem.findtext("vagas") or 0),
                    metragem_privativa=(elem.findtext("metragem_privativa") or "").strip(),
                    valor_a_partir=float(valor_str),
                    faixas_mcmv=faixas,
                    status=(elem.findtext("status") or "").strip(),
                    previsao_entrega=(elem.findtext("previsao_entrega") or "").strip(),
                    disponibilidade=int(disp_str),
                    diferencial=(elem.findtext("diferencial") or "").strip(),
                    foto=(elem.findtext("foto") or "").strip(),
                    link=(elem.findtext("link") or "").strip(),
                )
                novos_imoveis.append(imovel)

            if not novos_imoveis:
                raise ValueError("Nenhum imóvel válido encontrado na estrutura XML.")

            self._imoveis_cache = novos_imoveis
            self._ultima_atualizacao_ts = agora
            return True

        except Exception as exc:
            msg_alerta = (
                f"[ALERTA AUTOMAÇÃO] Falha ao atualizar XML ({exc}). "
                f"Mantida última versão válida com {len(self._imoveis_cache)} imóveis."
            )
            logger.warning(msg_alerta)
            self._alertas_automacao.append(msg_alerta)
            return False

    def listar_disponiveis(self) -> list[Imovel]:
        """Retorna apenas imóveis com disponibilidade > 0 e não vendidos."""
        self.recarregar_base(forcar=False)
        return [
            im
            for im in self._imoveis_cache
            if im.disponibilidade > 0 and _normalizar_texto(im.status) != "vendido"
        ]

    def listar_todos_admin(self) -> list[dict]:
        """Retorna todos os imóveis cadastrados (incluindo esgotados/vendidos) para a tela de gestão."""
        self.recarregar_base(forcar=False)
        return [asdict(im) for im in self._imoveis_cache]

    def _salvar_cache_em_xml(self) -> None:
        """Gera o arquivo XML formatado a partir da lista em memória e grava em disco."""
        from datetime import datetime
        from xml.sax.saxutils import escape

        agora_iso = datetime.now().isoformat(timespec="seconds")
        linhas = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<imoveis atualizacao="{agora_iso}">',
        ]
        for im in self._imoveis_cache:
            faixas_str = ", ".join(im.faixas_mcmv) if isinstance(im.faixas_mcmv, list) else str(im.faixas_mcmv)
            linhas.extend(
                [
                    "  <imovel>",
                    f"    <codigo>{escape(str(im.codigo))}</codigo>",
                    f"    <nome>{escape(str(im.nome))}</nome>",
                    f"    <cidade>{escape(str(im.cidade))}</cidade>",
                    f"    <bairro>{escape(str(im.bairro))}</bairro>",
                    f"    <endereco>{escape(str(im.endereco))}</endereco>",
                    f"    <tipo>{escape(str(im.tipo))}</tipo>",
                    f"    <tipologia>{escape(str(im.tipologia))}</tipologia>",
                    f"    <dormitorios>{int(im.dormitorios)}</dormitorios>",
                    f"    <suites>{int(im.suites)}</suites>",
                    f"    <vagas>{int(im.vagas)}</vagas>",
                    f"    <metragem_privativa>{escape(str(im.metragem_privativa))}</metragem_privativa>",
                    f"    <valor_a_partir>{float(im.valor_a_partir):.2f}</valor_a_partir>",
                    f"    <faixas_mcmv>{escape(faixas_str)}</faixas_mcmv>",
                    f"    <status>{escape(str(im.status))}</status>",
                    f"    <previsao_entrega>{escape(str(im.previsao_entrega))}</previsao_entrega>",
                    f"    <disponibilidade>{int(im.disponibilidade)}</disponibilidade>",
                    f"    <diferencial>{escape(str(im.diferencial))}</diferencial>",
                    f"    <foto>{escape(str(im.foto))}</foto>",
                    f"    <link>{escape(str(im.link))}</link>",
                    "  </imovel>",
                ]
            )
        linhas.append("</imoveis>")
        xml_final = "\n".join(linhas) + "\n"
        self.xml_path.parent.mkdir(parents=True, exist_ok=True)
        self.xml_path.write_text(xml_final, encoding="utf-8")
        self._ultima_atualizacao_ts = time.time()

    def salvar_ou_atualizar_imovel(self, dados: dict) -> dict:
        """
        Cria um novo imóvel ou atualiza um existente pelo código através do formulário amigável,
        gerando e salvando automaticamente o XML oficial nos bastidores.
        """
        self.recarregar_base(forcar=False)
        codigo = (dados.get("codigo") or "").strip().upper()
        cidade = (dados.get("cidade") or "Tubarão").strip()

        if not codigo:
            prefixo = "TUB" if "tubar" in _normalizar_texto(cidade) else "CAP" if "capiv" in _normalizar_texto(cidade) else "PES"
            codigo = f"IMOB-{prefixo}-{len(self._imoveis_cache) + 1:03d}"

        faixas_in = dados.get("faixas_mcmv", ["Faixa 1", "Faixa 2", "Faixa 3"])
        if isinstance(faixas_in, str):
            faixas_lista = [f.strip() for f in faixas_in.split(",") if f.strip()]
        else:
            faixas_lista = [str(f).strip() for f in faixas_in if str(f).strip()]

        novo_imovel = Imovel(
            codigo=codigo,
            nome=(dados.get("nome") or "").strip(),
            cidade=cidade,
            bairro=(dados.get("bairro") or "").strip(),
            endereco=(dados.get("endereco") or "").strip(),
            tipo=(dados.get("tipo") or "Apartamento").strip(),
            tipologia=(dados.get("tipologia") or "").strip(),
            dormitorios=int(dados.get("dormitorios") or 2),
            suites=int(dados.get("suites") or 0),
            vagas=int(dados.get("vagas") or 1),
            metragem_privativa=(dados.get("metragem_privativa") or "").strip(),
            valor_a_partir=float(dados.get("valor_a_partir") or 0.0),
            faixas_mcmv=faixas_lista,
            status=(dados.get("status") or "Em obra").strip(),
            previsao_entrega=(dados.get("previsao_entrega") or "").strip(),
            disponibilidade=int(dados.get("disponibilidade") or 0),
            diferencial=(dados.get("diferencial") or "").strip(),
            foto=(dados.get("foto") or "").strip(),
            link=(dados.get("link") or "").strip(),
        )

        substituiu = False
        for i, existente in enumerate(self._imoveis_cache):
            if existente.codigo.upper() == codigo:
                self._imoveis_cache[i] = novo_imovel
                substituiu = True
                break

        if not substituiu:
            self._imoveis_cache.append(novo_imovel)

        self._salvar_cache_em_xml()
        return {
            "status": "atualizado" if substituiu else "criado",
            "imovel": asdict(novo_imovel),
            "total_imoveis": len(self._imoveis_cache),
        }

    def remover_imovel(self, codigo: str) -> dict:
        """Remove um imóvel pelo código e atualiza o arquivo XML."""
        self.recarregar_base(forcar=False)
        cod_norm = codigo.strip().upper()
        antes = len(self._imoveis_cache)
        self._imoveis_cache = [im for im in self._imoveis_cache if im.codigo.upper() != cod_norm]
        removido = len(self._imoveis_cache) < antes
        if removido:
            self._salvar_cache_em_xml()
        return {
            "removido": removido,
            "codigo": cod_norm,
            "total_imoveis": len(self._imoveis_cache),
        }

    def detalhar_imovel(self, codigo: str) -> Optional[dict]:
        """Retorna a ficha completa de um empreendimento pelo código."""
        codigo_norm = codigo.strip().upper()
        for im in self.listar_disponiveis():
            if im.codigo.upper() == codigo_norm:
                dados = asdict(im)
                dados.update(im.formatar_apresentacao())
                return dados
        return None

    def buscar_imoveis(
        self,
        cidade: Optional[str] = None,
        bairro: Optional[str] = None,
        tipo: Optional[str] = None,
        quartos: Optional[int] = None,
        valor_maximo: Optional[float] = None,
        faixa_mcmv: Optional[str] = None,
        renda_bruta: Optional[float] = None,
        status_entrega: Optional[str] = None,
    ) -> dict:
        """
        Consulta a base XML vigente aplicando filtros estritos de estoque e teto MCMV.
        Se não houver opção exata, retorna as opções mais próximas dentro do teto
        explicando a diferença ('fica na cidade vizinha', 'é casa com 2 quartos', etc.).
        """
        disponiveis = self.listar_disponiveis()
        regra_mcmv = obter_regra_por_faixa_ou_renda(
            renda_bruta=renda_bruta,
            faixa_informada=faixa_mcmv,
        )

        # Filtra primeiro pelo teto MCMV da cidade de cada imóvel (regra inegociável)
        candidatos_no_teto: list[Imovel] = []
        for im in disponiveis:
            if regra_mcmv is not None:
                teto_imovel_cidade = obter_teto_cidade(regra_mcmv, im.cidade)
                if im.valor_a_partir > teto_imovel_cidade:
                    continue
            if valor_maximo is not None and im.valor_a_partir > valor_maximo:
                continue
            candidatos_no_teto.append(im)

        cidade_norm = _normalizar_texto(cidade or "")
        cidade_especifica = cidade_norm not in (
            "",
            "qualquer",
            "aberto",
            "todas",
            "tanto faz",
        )
        bairro_norm = _normalizar_texto(bairro or "")
        tipo_norm = _normalizar_texto(tipo or "")
        status_norm = _normalizar_texto(status_entrega or "")

        exatos: list[Imovel] = []
        proximos: list[tuple[Imovel, str]] = []

        for im in candidatos_no_teto:
            diferencas: list[str] = []

            if cidade_especifica and cidade_norm not in _normalizar_texto(im.cidade):
                diferencas.append(f"fica na cidade vizinha ({im.cidade})")

            if bairro_norm and bairro_norm not in _normalizar_texto(im.bairro):
                diferencas.append(f"fica no bairro {im.bairro}")

            if tipo_norm and tipo_norm not in _normalizar_texto(im.tipo):
                diferencas.append(f"é do tipo {im.tipo.lower()}")

            if quartos is not None and im.dormitorios != quartos:
                diferencas.append(f"tem {im.dormitorios} quartos")

            if status_norm and status_norm not in _normalizar_texto(im.status):
                diferencas.append(f"está com status '{im.status}'")

            if not diferencas:
                exatos.append(im)
            else:
                proximos.append((im, ", ".join(diferencas)))

        # Ordena da mais adequada/menor valor para maior
        exatos.sort(key=lambda x: x.valor_a_partir)
        proximos.sort(key=lambda x: (len(x[1].split(",")), x[0].valor_a_partir))

        if exatos:
            return {
                "encontrou_opcao_exata": True,
                "total_encontrados": len(exatos),
                "imoveis": [im.formatar_apresentacao() for im in exatos],
                "opcoes_proximas_complementares": [
                    im.formatar_apresentacao(obs) for im, obs in proximos[:2]
                ],
                "orientacao_lili": (
                    "Apresente as opções compatíveis ancorando no sonho/benefício, "
                    "sempre informando 'a partir de' e 'sujeito à disponibilidade'."
                ),
            }

        if proximos:
            return {
                "encontrou_opcao_exata": False,
                "total_encontrados": len(proximos[:3]),
                "imoveis": [im.formatar_apresentacao(obs) for im, obs in proximos[:3]],
                "orientacao_lili": (
                    "Não há opção exata para todos os filtros, mas existem opções muito próximas "
                    "dentro do teto MCMV. Ofereça a mais próxima explicando a diferença com transparência."
                ),
            }

        return {
            "encontrou_opcao_exata": False,
            "total_encontrados": 0,
            "imoveis": [],
            "orientacao_lili": (
                "Nenhuma opção compatível no estoque atual. Informe com transparência, "
                "registre a demanda no CRM e ofereça avisar quando surgir algo."
            ),
        }
