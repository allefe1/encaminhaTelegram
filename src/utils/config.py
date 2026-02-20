"""
Configurações do Bot Clone Telegram
"""
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Credenciais da API do Telegram
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Opcional

# Validação
if not API_ID or not API_HASH:
    raise ValueError(
        "❌ API_ID e API_HASH são obrigatórios!\n"
        "   1. Acesse https://my.telegram.org\n"
        "   2. Crie uma aplicação\n"
        "   3. Copie o .env.example para .env e preencha os valores"
    )

API_ID = int(API_ID)
