"""Leitura eficiente do CSV de resultado do RuFaS.

O arquivo pode ter milhares de colunas e ~1GB, então nunca carregamos tudo:
primeiro lemos só o cabeçalho para montar os filtros, depois carregamos
apenas as colunas selecionadas pelo usuário.
"""

import os
import tempfile

import pandas as pd
import streamlit as st


@st.cache_resource(show_spinner=False)
def save_uploaded_file(uploaded_file) -> str:
    """Salva o arquivo enviado via st.file_uploader em disco e retorna o
    caminho. Cacheado pelo próprio uploaded_file (Streamlit já sabe hashear
    esse tipo), então um novo upload gera um novo arquivo."""
    suffix = os.path.splitext(uploaded_file.name)[1] or ".csv"
    fd, path = tempfile.mkstemp(prefix="rufas_upload_", suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


@st.cache_data(show_spinner=False)
def get_columns(path: str, _mtime: float) -> list[str]:
    header = pd.read_csv(path, nrows=0, encoding="utf-8")
    return list(header.columns)


@st.cache_data(show_spinner=False)
def load_data(path: str, _mtime: float, columns: tuple[str, ...]) -> pd.DataFrame:
    # low_memory=False evita um IndexError do parser C do pandas 3.0.5 ao ler,
    # via usecols, colunas esparsas cujo valor é um repr de objeto Python
    # complexo (ex.: avg_essential_amino_acid_requirement).
    return pd.read_csv(path, usecols=list(columns), encoding="utf-8", low_memory=False)


def read_columns(path: str) -> list[str]:
    return get_columns(path, os.path.getmtime(path))


def read_data(path: str, columns: list[str]) -> pd.DataFrame:
    return load_data(path, os.path.getmtime(path), tuple(columns))
