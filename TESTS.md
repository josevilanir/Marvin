# Execução de Testes Automatizados no Marvin

Este documento descreve como executar os testes automatizados do projeto Marvin e como visualizar os resultados por meio de relatórios em HTML.

---

## 📦 Pré-requisitos

Certifique-se de que as seguintes dependências estão instaladas no ambiente virtual (`venv`):

```bash
pip install pytest pytest-html
```

---

## ▶️ Executando os Testes

Para rodar todos os testes localizados em `backend/tests/services`, execute o seguinte comando a partir do diretório do projeto:

```bash
pytest backend/tests/services
```

---

## 📄 Gerando Relatório em HTML

Para gerar um relatório visual com os resultados dos testes:

```bash
pytest backend/tests/services --html=report.html --self-contained-html
```

Esse comando criará um arquivo `report.html` no mesmo diretório. Para abrir:

1. Localize o arquivo `report.html`.
2. Abra-o no navegador de sua preferência (ex: Chrome, Firefox, Edge).

---

## ✅ Interpretação dos Resultados

- ✅ **Verde**: Teste passou com sucesso.
- ❌ **Vermelho**: Teste falhou; verifique as mensagens de erro no relatório.
- ⚠️ **Amarelo/Cinza**: Teste foi ignorado ou não foi executado.

---

## 💡 Dica Extra

Durante o desenvolvimento, é útil rodar apenas um arquivo de teste específico:

```bash
pytest backend/tests/services/test_spotify_service.py
```

---

## 📌 Observações

- O parâmetro `--self-contained-html` garante que o relatório seja gerado como um único arquivo independente.
- Caso esteja executando os testes dentro de um container ou Codespace, baixe o `report.html` para sua máquina local para visualizar no navegador.