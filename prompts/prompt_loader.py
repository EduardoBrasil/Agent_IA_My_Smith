import os
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

def load_prompt(prompt_name: str) -> str:
    """
    Carrega o texto de um prompt pelo nome do arquivo (sem extensão).
    Exemplo: load_prompt('release_tecnologia')
    """
    path = PROMPTS_DIR / f"{prompt_name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt '{prompt_name}' não encontrado em {PROMPTS_DIR}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
