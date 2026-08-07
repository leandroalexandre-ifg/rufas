# Dashboard de Resultados do RuFaS

Dashboard local/web para explorar resultados de simulações do
[RuFaS](https://rufas.org) (Ruminant Farm Systems) sem precisar mexer em
código ou linha de comando.

Este é o **primeiro marco** de um projeto maior — cobre só a **visualização**
de um CSV de resultado já gerado por uma simulação anterior. Não roda o
modelo RuFaS, não gera arquivos de entrada e não faz "match" de planilhas.

## O que o dashboard faz

1. **Upload** do CSV de resultado da simulação (arrastar e soltar ou
   selecionar o arquivo — suporta até 1GB).
2. **Filtro** das variáveis a exibir, de duas formas complementares:
   - **Amigável**: menus de módulo (`AnimalModuleReporter`, `FieldDataReporter`,
     etc.) e palavra-chave temática (milk, methane, population...).
   - **Regex**: o padrão gerado pelo filtro amigável aparece num campo de
     texto editável — o mesmo mecanismo que o RuFaS usa nativamente em
     `output/output_filters/`.
3. **Tabela** navegável com as colunas selecionadas.
4. **Gráficos** de série temporal (eixo X = dia de simulação) para até 3
   variáveis por vez, escolhidas manualmente num seletor — nada é plotado
   automaticamente. Variáveis que não fazem sentido como série temporal
   (identificadores, booleanos, texto) ficam de fora do seletor de gráfico,
   mas continuam visíveis na tabela; variáveis numéricas de baixa
   cardinalidade aparecem marcadas como "possivelmente categórica" em vez
   de serem escondidas.

## Como rodar localmente

```bash
cd dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`.

## Formato esperado do CSV

O arquivo de entrada é uma **saída** do RuFaS (o resultado da simulação),
tipicamente com milhares de colunas e centenas de milhares de linhas. Nomes
de coluna seguem o padrão `Módulo.método.variável (unidade)`, por exemplo:

```
AnimalModuleReporter.report_animal_population_statistics.population_number_of_lactating_cows (animals)
```

Muitas células ficam vazias — nem toda variável é reportada em todo
registro, o que é esperado (esparsidade real do modelo, não erro).

## Deploy (Streamlit Community Cloud)

O app está publicado a partir deste repositório — qualquer push em `main`
republica automaticamente.

A fonte de dados é **só upload manual**. Já tentamos carregamento
automático via link do Google Drive, mas descartamos: o download de um CSV
real (~900MB) derrubava o app publicado (limite de memória/tempo do plano
gratuito), enquanto o mesmo arquivo via upload sempre funcionou. Detalhes
da investigação (e por que reduzir o CSV por colunas não ajudaria) estão no
`CLAUDE.md` do repositório principal.

Configuração relevante em `.streamlit/config.toml`: `maxUploadSize = 1024`
(o padrão do Streamlit é ~200MB, insuficiente para os CSVs reais).

## Estrutura do projeto

```
dashboard/
├── app.py            # Entrypoint Streamlit — fluxo da interface
├── data_loader.py     # Leitura eficiente do CSV (upload, cabeçalho, colunas selecionadas)
├── filters.py          # Lógica de filtro (módulo/palavra-chave/regex) e classificação de variáveis
├── requirements.txt
└── .streamlit/
    └── config.toml    # maxUploadSize
```

## Limitações conhecidas

- Upload de arquivos grandes depende da velocidade de upload da internet de
  quem está usando o app — isso é inerente ao Streamlit Community Cloud e
  não tem correção possível no código.
- Sem persistência entre reinícios do app: cada reinício do processo no
  Streamlit Cloud limpa o cache, e o CSV precisa ser reenviado.
