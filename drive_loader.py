"""Download do CSV de resultado a partir de um link do Google Drive."""

import os
import re
import tempfile

import gdown
import streamlit as st

# Cobre os formatos que o Drive gera ao compartilhar um arquivo:
#   .../file/d/FILE_ID/view?usp=sharing
#   .../open?id=FILE_ID
#   .../uc?id=FILE_ID&export=download
_DRIVE_ID_PATTERN = re.compile(r"/d/([a-zA-Z0-9_-]{10,})|[?&]id=([a-zA-Z0-9_-]{10,})")
_BARE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{10,}$")


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


@st.cache_resource(show_spinner=False)
def download_from_drive(file_id: str) -> str:
    """Baixa o CSV do Drive para um arquivo temporário e retorna o caminho.

    Cacheado por file_id: o download só acontece uma vez por processo,
    compartilhado entre todas as sessões do app. gdown lida sozinho com a
    tela de confirmação que o Drive mostra para arquivos grandes.
    """
    # Passamos id= (já extraído nós mesmos via extract_drive_file_id), então
    # não precisamos do parsing de URL do gdown — e esta versão do gdown
    # nem aceita fuzzy= junto com id=.
    path = os.path.join(tempfile.gettempdir(), f"rufas_drive_{file_id}.csv")
    gdown.download(id=file_id, output=path, quiet=True)
    if not os.path.isfile(path):
        raise RuntimeError("O download não gerou nenhum arquivo — confira se o link é público.")
    return path
