import asyncio
import traceback
import random
from pyrogram import Client
from pyrogram.raw import functions as raw_functions
from src.utils.logger import get_logger

logger = get_logger()


class Cloner:
    def __init__(self, client: Client):
        self.client = client
        self.stop_requested = False
        self.pause_requested = False
        self.is_running = False

    async def _copy_message(self, msg, destination_chat_id):
        """
        Tenta copiar uma mensagem usando multiplas estrategias.
        ZERO filtros previos - tenta copiar TUDO, igual ao codigo original.
        Retorna (True, None) se copiou, (False, motivo) se falhou.
        """

        errors = []

        # Estrategia 1: copy() - metodo padrao
        try:
            await msg.copy(chat_id=destination_chat_id)
            return True, None
        except Exception as e1:
            errors.append(f"copy: {e1}")

        # Estrategia 2: Re-enviar com formatacao e markup
        try:
            sent = await self._resend_content(msg, destination_chat_id, skip_markup=False)
            if sent:
                return True, None
        except Exception as e3:
            errors.append(f"resend: {e3}")

        # Estrategia 3: Re-enviar SEM reply_markup
        try:
            sent = await self._resend_content(msg, destination_chat_id, skip_markup=True)
            if sent:
                return True, None
        except Exception as e4:
            errors.append(f"resend_limpo: {e4}")

        # Estrategia 4: Texto puro sem formatacao
        try:
            text = msg.text or msg.caption or ""
            if text.strip():
                await self.client.send_message(
                    chat_id=destination_chat_id,
                    text=text,
                )
                return True, None
        except Exception as e5:
            errors.append(f"texto_puro: {e5}")

        # Estrategia 5: Forward via API crua COM drop_author=True
        # Encaminha no nivel do protocolo Telegram SEM mostrar origem
        try:
            from_peer = await self.client.resolve_peer(msg.chat.id)
            to_peer = await self.client.resolve_peer(destination_chat_id)
            await self.client.invoke(
                raw_functions.messages.ForwardMessages(
                    from_peer=from_peer,
                    id=[msg.id],
                    to_peer=to_peer,
                    random_id=[random.randint(-(2**63), 2**63 - 1)],
                    drop_author=True,
                    silent=True,
                )
            )
            return True, None
        except Exception as e6:
            errors.append(f"raw_forward: {e6}")

        # Diagnostico detalhado
        msg_info = self._get_msg_info(msg)
        return False, f"{msg_info} -> {' | '.join(errors)}"

    def _get_msg_info(self, msg):
        """Retorna info de diagnostico sobre a mensagem."""
        parts = [f"id={msg.id}"]
        if msg.text:
            parts.append(f"text='{msg.text[:40]}'")
        if msg.caption:
            parts.append(f"caption='{msg.caption[:40]}'")
        if msg.media:
            parts.append(f"media={msg.media}")
        if msg.service:
            parts.append("service=True")
        if msg.empty:
            parts.append("empty=True")
        if msg.web_page:
            parts.append("web_page=True")
        if msg.reply_markup:
            parts.append("reply_markup=True")
        if msg.entities:
            types = [e.type.name for e in msg.entities[:3]]
            parts.append(f"entities={types}")
        if msg.forward_date:
            parts.append("forwarded=True")
        return "[" + ", ".join(parts) + "]"

    async def _resend_content(self, msg, destination_chat_id, skip_markup=False):
        """Re-envia o conteudo da mensagem preservando formatacao."""

        caption = msg.caption or ""
        caption_entities = msg.caption_entities if not skip_markup else None
        reply_markup = None if skip_markup else msg.reply_markup

        # Foto
        if msg.photo:
            kwargs = {"chat_id": destination_chat_id, "photo": msg.photo.file_id, "caption": caption}
            if caption_entities:
                kwargs["caption_entities"] = caption_entities
            if reply_markup:
                kwargs["reply_markup"] = reply_markup
            await self.client.send_photo(**kwargs)
            return True

        # Video
        if msg.video:
            kwargs = {"chat_id": destination_chat_id, "video": msg.video.file_id, "caption": caption}
            if caption_entities:
                kwargs["caption_entities"] = caption_entities
            if reply_markup:
                kwargs["reply_markup"] = reply_markup
            await self.client.send_video(**kwargs)
            return True

        # Documento
        if msg.document:
            kwargs = {"chat_id": destination_chat_id, "document": msg.document.file_id, "caption": caption}
            if caption_entities:
                kwargs["caption_entities"] = caption_entities
            if reply_markup:
                kwargs["reply_markup"] = reply_markup
            await self.client.send_document(**kwargs)
            return True

        # Audio
        if msg.audio:
            kwargs = {"chat_id": destination_chat_id, "audio": msg.audio.file_id, "caption": caption}
            if caption_entities:
                kwargs["caption_entities"] = caption_entities
            if reply_markup:
                kwargs["reply_markup"] = reply_markup
            await self.client.send_audio(**kwargs)
            return True

        # Voz
        if msg.voice:
            kwargs = {"chat_id": destination_chat_id, "voice": msg.voice.file_id, "caption": caption}
            if caption_entities:
                kwargs["caption_entities"] = caption_entities
            if reply_markup:
                kwargs["reply_markup"] = reply_markup
            await self.client.send_voice(**kwargs)
            return True

        # Sticker
        if msg.sticker:
            kwargs = {"chat_id": destination_chat_id, "sticker": msg.sticker.file_id}
            if reply_markup:
                kwargs["reply_markup"] = reply_markup
            await self.client.send_sticker(**kwargs)
            return True

        # Video nota (bolinha)
        if msg.video_note:
            kwargs = {"chat_id": destination_chat_id, "video_note": msg.video_note.file_id}
            if reply_markup:
                kwargs["reply_markup"] = reply_markup
            await self.client.send_video_note(**kwargs)
            return True

        # Animacao (GIF)
        if msg.animation:
            kwargs = {"chat_id": destination_chat_id, "animation": msg.animation.file_id, "caption": caption}
            if caption_entities:
                kwargs["caption_entities"] = caption_entities
            if reply_markup:
                kwargs["reply_markup"] = reply_markup
            await self.client.send_animation(**kwargs)
            return True

        # Texto COM entidades (hashtags, bold, links)
        if msg.text:
            kwargs = {"chat_id": destination_chat_id, "text": msg.text}
            if not skip_markup and msg.entities:
                kwargs["entities"] = msg.entities
            if reply_markup:
                kwargs["reply_markup"] = reply_markup
            await self.client.send_message(**kwargs)
            return True

        return False

    async def clone_chat(self,
                         origin_chat_id: int,
                         destination_chat_id: int,
                         progress_callback=None,
                         log_callback=None):
        """Clona mensagens da origem para o destino."""
        self.stop_requested = False
        self.pause_requested = False
        self.is_running = True

        async def log(msg, level="info"):
            if log_callback:
                await log_callback(msg, level)
            if level == "error":
                logger.error(msg)
            else:
                logger.info(msg)

        try:
            await log("Analisando canal de origem...")

            # Contar total de mensagens
            total_messages = 0
            async for _ in self.client.get_chat_history(origin_chat_id):
                total_messages += 1

            await log(f"Encontradas {total_messages} mensagens para clonar.")

            if total_messages == 0:
                await log("Canal de origem esta vazio!", "warning")
                self.is_running = False
                return

            # Coletar mensagens
            await log("Coletando mensagens...")
            messages = []
            async for msg in self.client.get_chat_history(origin_chat_id):
                messages.append(msg)

            # Inverter para enviar da mais antiga para a mais recente
            messages.reverse()
            await log("Iniciando clonagem...")

            copied_count = 0
            failed_count = 0
            failed_details = []

            for i, msg in enumerate(messages):
                # Verificar cancelamento
                if self.stop_requested:
                    await log(f"Clonagem cancelada! Copiadas: {copied_count}", "warning")
                    break

                # Verificar pausa
                while self.pause_requested:
                    await asyncio.sleep(0.5)
                    if self.stop_requested:
                        await log("Clonagem cancelada durante pausa!", "warning")
                        self.is_running = False
                        return

                try:
                    success, reason = await self._copy_message(msg, destination_chat_id)

                    if success:
                        copied_count += 1
                    else:
                        failed_count += 1
                        if len(failed_details) < 15:
                            failed_details.append(reason)
                        logger.warning(f"Mensagem nao copiada: {reason}")

                    # Atualizar progresso
                    if progress_callback:
                        await progress_callback(i + 1, total_messages)

                    # Log a cada 10 mensagens copiadas
                    if copied_count > 0 and copied_count % 10 == 0:
                        await log(f"Progresso: {copied_count}/{total_messages} mensagens copiadas")

                    # Limite de taxa
                    await asyncio.sleep(0.5)

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Excecao inesperada msg {msg.id}: {traceback.format_exc()}")

            # Resumo final
            summary = f"Copiadas: {copied_count}"
            if failed_count > 0:
                summary += f", Falhas: {failed_count}"

            if not self.stop_requested:
                await log(f"Clonagem finalizada! {summary}", "success")

            # Mostrar detalhes das falhas no log
            if failed_details:
                await log(f"--- Detalhes de {len(failed_details)} mensagens com falha ---", "warning")
                for detail in failed_details:
                    await log(detail, "warning")

            # Progresso final
            if progress_callback:
                await progress_callback(total_messages, total_messages)

        except Exception as e:
            await log(f"Erro critico: {str(e)}", "error")
            logger.error(traceback.format_exc())
        finally:
            self.is_running = False

    def stop(self):
        self.stop_requested = True
        self.pause_requested = False

    def pause(self):
        self.pause_requested = True

    def resume(self):
        self.pause_requested = False
