import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

PROMPTS_DIR = Path(__file__).parent / 'prompts'
OUTPUTS_DIR = Path(__file__).parent / 'outputs'

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY)

PROMPT_FILES = {
    'cliente': 'cliente.txt',
    'comercial': 'comercial.txt',
    'suporte': 'suporte.txt',
}

def read_prompt(prompt_name):
    path = PROMPTS_DIR / PROMPT_FILES[prompt_name]
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_document(prompt_template, user_message, output_path):
    print("DEBUG OPENAI_API_KEY:", repr(OPENAI_API_KEY))
    prompt = prompt_template.replace('{mensagem}', user_message)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )
    content = response.choices[0].message.content
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

def generate_documents(user_message):
    OUTPUTS_DIR.mkdir(exist_ok=True)
    for name in PROMPT_FILES:
        prompt_template = read_prompt(name)
        output_path = OUTPUTS_DIR / f'{name}_output.txt'
        generate_document(prompt_template, user_message, output_path)