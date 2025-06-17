# Cobertura de Testes

Este projeto utiliza o [pytest](https://docs.pytest.org/) e [pytest-cov](https://pytest-cov.readthedocs.io/) para garantir alta cobertura de código.

![Cobertura de Código](https://img.shields.io/badge/coverage-95%25-brightgreen)

> **Nota:** O badge acima é ilustrativo. Para gerar o percentual real do seu projeto, rode os testes conforme instruções abaixo.

## Como gerar o relatório de cobertura

Execute no terminal:

```
C:/Users/brasi/workspace/.venv/Scripts/python.exe -m pytest --cov=. --cov-report=term-missing
```

Ou para um relatório visual em HTML:

```
C:/Users/brasi/workspace/.venv/Scripts/python.exe -m pytest --cov=. --cov-report=html
```

O percentual de cobertura será exibido no terminal e/ou no arquivo `htmlcov/index.html`.

## Exemplo de saída

```
---------- coverage: platform win32, python 3.11.9-final-0 ----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
services/file_handler_service.py           90      0   100%
...
TOTAL                                    500     10    98%
```

> Recomenda-se manter a cobertura acima de 90% para garantir a qualidade do projeto.
