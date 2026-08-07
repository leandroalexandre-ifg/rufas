"""Download do CSV de resultado a partir de um link do Google Drive."""

import os
import re
import tempfile

import gdown
import requests
import streamlit as st

# Cobre os formatos que o Drive gera ao compartilhar um arquivo:
#   .../file/d/FILE_ID/view?usp=sharing
#   .../open?id=FILE_ID
#   .../uc?id=FILE_ID&export=download
_DRIVE_ID_PATTERN = re.compile(r"/d/([a-zA-Z0-9_-]{10,})|[?&]id=([a-zA-Z0-9_-]{10,})")
_BARE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{10,}$")

# Abaixo disso, quase certo que o Drive devolveu uma página de erro/confirmação
# em vez do CSV de verdade (o menor CSV real que vimos tem centenas de MB).
_MIN_VALID_FILE_SIZE_BYTES = 10_000
_SNIFF_BYTES = 512


class DriveDownloadError(Exception):
    """Erro ao baixar ou validar o arquivo do Google Drive."""


def extract_drive_file_id(text: str) -> str | None:
    """Extrai o FILE_ID de um link de compartilhamento do Google Drive.

    Também aceita que o usuário cole só o ID puro.
    """
    text = text.strip()
    if not text:
        return None
    match = _DRIVE_ID_PATTERN.search(text)
    if match:
        return match.group(1) or match.group(2)
    if _BARE_ID_PATTERN.match(text):
        return text
    return None


def _looks_like_html(path: str) -> bool:
    with open(path, "rb") as f:
        head = f.read(_SNIFF_BYTES).strip().lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html")


def _validate_downloaded_file(path: str) -> None:
    """Detecta o caso conhecido de o Drive devolver uma página de aviso em
    vez do arquivo — sem isso, um download 'bem-sucedido' pode na verdade
    ser um HTML de alguns KB que quebra tudo silenciosamente mais adiante."""
    if not os.path.isfile(path):
        raise DriveDownloadError("o download não gerou nenhum arquivo.")
    size = os.path.getsize(path)
    if size < _MIN_VALID_FILE_SIZE_BYTES:
        raise DriveDownloadError(
            f"o arquivo baixado tem só {size} bytes — provavelmente o Drive "
            "devolveu uma página de aviso/erro em vez do CSV. Confira se a "
            "permissão do arquivo é \"Qualquer pessoa com o link\"."
        )
    if _looks_like_html(path):
        raise DriveDownloadError(
            "o conteúdo baixado parece ser uma página HTML do Drive, não o "
            "CSV esperado. Confira se a permissão do arquivo é \"Qualquer "
            "pessoa com o link\"."
        )


def _download_via_gdown(file_id: str, path: str) -> None:
    # Sem fuzzy=: passamos id= diretamente (já extraído por nós), e esta
    # versão do gdown nem aceita fuzzy= junto com id=. A tela de confirmação
    # de arquivo grande já é tratada internamente pelo gdown nesse caminho.
    gdown.download(id=file_id, output=path, quiet=True)


def _download_via_requests_fallback(file_id: str, path: str) -> None:
    """Contorna manualmente a confirmação de arquivo grande do Drive.
    Usado só se o gdown falhar ou devolver algo inválido — reforço, não
    o caminho principal."""
    url = "https://drive.usercontent.google.com/download"
    params = {"id": file_id, "export": "download", "confirm": "t"}
    with requests.Session() as session:
        with session.get(url, params=params, stream=True, timeout=30) as response:
            response.raise_for_status()
            with open(path, "wb") as f:
                for chunk in response.iter_content(chunk_size=512 * 1024):
                    f.write(chunk)


@st.cache_resource(show_spinner=False)
def download_from_drive(file_id: str) -> str:
    """Baixa o CSV do Drive para um arquivo temporário e retorna o caminho.

    Tenta o gdown primeiro; se falhar ou o resultado parecer inválido
    (página HTML em vez do CSV), tenta um download manual via requests como
    reforço. Cacheado por file_id: o download só acontece uma vez por
    processo, compartilhado entre todas as sessões do app. Nunca deixa uma
    exceção "esquisita" escapar sem mensagem — sempre levanta
    DriveDownloadError com o motivo real.
    """
    path = os.path.join(tempfile.gettempdir(), f"rufas_drive_{file_id}.csv")

    attempts = [("gdown", _download_via_gdown), ("download direto", _download_via_requests_fallback)]
    errors = []
    for name, download_fn in attempts:
        try:
            download_fn(file_id, path)
            _validate_downloaded_file(path)
            return path
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    raise DriveDownloadError(
        "nenhum dos métodos de download funcionou.\n" + "\n".join(f"- {e}" for e in errors)
    )
