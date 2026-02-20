import asyncio
import os
import sqlite3
from pyrogram import Client
from pyrogram.enums import ChatType
from src.utils.config import API_ID, API_HASH
from src.utils.logger import get_logger

logger = get_logger()

SESSION_NAME = "telegram_clone_session"


class TelegramClient:
    def __init__(self):
        self.app = Client(
            SESSION_NAME,
            api_id=API_ID,
            api_hash=API_HASH
        )
        self.is_connected = False
        self.is_authorized = False

    def _has_valid_session(self):
        """Verifica se existe uma sessao com usuario autenticado."""
        session_file = f"{SESSION_NAME}.session"
        if not os.path.exists(session_file):
            return False
        try:
            conn = sqlite3.connect(session_file)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM sessions LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            # user_id != 0 e != None significa autenticado
            return row is not None and row[0] is not None and row[0] != 0
        except Exception:
            return False

    async def try_connect(self):
        """Conecta ao Telegram. Retorna usuario se ja autenticado."""

        has_session = self._has_valid_session()

        if has_session:
            # Tem sessao valida, tenta start() para reautenticar
            try:
                await self.app.start()
                self.is_connected = True
                self.is_authorized = True
                me = await self.app.get_me()
                logger.info(f"Conectado como {me.first_name} (@{me.username})")
                return me
            except Exception as e:
                error_msg = str(e)
                logger.info(f"Sessao invalida: {error_msg}")

                # Sessao corrompida, limpa e faz login manual
                if "AUTH_KEY" in error_msg:
                    self._delete_session()

                # Tenta desconectar o client que falhou
                try:
                    await self.app.disconnect()
                except Exception:
                    pass

                # Recria o client para um estado limpo
                self.app = Client(
                    SESSION_NAME,
                    api_id=API_ID,
                    api_hash=API_HASH
                )

        # Conecta via TCP para login manual
        try:
            await self.app.connect()
            self.is_connected = True
            self.is_authorized = False
            logger.info("Conexao TCP estabelecida, aguardando autenticacao...")
        except Exception as conn_err:
            logger.error(f"Falha na conexao TCP: {conn_err}")
            self.is_connected = False
        return None

    def _delete_session(self):
        """Deleta o arquivo de sessao corrompido/expirado."""
        session_file = f"{SESSION_NAME}.session"
        journal_file = f"{SESSION_NAME}.session-journal"
        for f in [session_file, journal_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                    logger.info(f"Removido: {f}")
                except Exception as e:
                    logger.error(f"Erro ao remover {f}: {e}")

    async def disconnect(self):
        """Desconecta do Telegram."""
        if self.is_connected:
            try:
                if self.is_authorized:
                    await self.app.stop()
                else:
                    await self.app.disconnect()
            except Exception:
                pass
            self.is_connected = False
            self.is_authorized = False
            logger.info("Desconectado do Telegram")

    async def get_channels(self):
        """Retorna a lista de canais e supergrupos disponiveis."""
        if not self.is_authorized:
            return []

        channels = []
        try:
            async for dialog in self.app.get_dialogs():
                chat = dialog.chat
                if chat.type in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
                    channels.append({
                        "id": chat.id,
                        "title": chat.title or "Sem titulo",
                        "type": "Canal" if chat.type == ChatType.CHANNEL else "Grupo",
                        "username": f"@{chat.username}" if chat.username else "Privado",
                        "member_count": chat.members_count or 0
                    })
        except Exception as e:
            logger.error(f"Erro ao carregar canais: {e}")
        return channels
