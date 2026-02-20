import flet as ft
from flet import Colors as colors, Icons as icons
import asyncio
import traceback
from pyrogram import types as pyrogram_types
from src.core.client import TelegramClient
from src.core.cloner import Cloner
from src.utils.logger import get_logger
from src.ui.components import (
    BG_COLOR, SURFACE_COLOR, PRIMARY_ACCENT, WHITE, SECONDARY_TEXT,
    StatsCard, SelectionTile, PrimaryButton, LogItem,
)

logger = get_logger()


class DarkoGramApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "DarkoGram"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = BG_COLOR
        self.page.padding = 0

        # Flet 0.80+ window API
        self.page.window.width = 1100
        self.page.window.height = 750

        self.client = TelegramClient()
        self.cloner = None  # Criado apos conexao

        self.channels = []
        self.source_channel = None
        self.dest_channel = None

        self.init_ui()

    def _ensure_cloner(self):
        """Garante que o Cloner usa o Client atual."""
        self.cloner = Cloner(self.client.app)

    def init_ui(self):
        self.show_loading("Conectando ao Telegram...")
        self.page.run_task(self.check_connection)

    async def check_connection(self):
        try:
            me = await self.client.try_connect()
            if me:
                # Mostra o dashboard IMEDIATAMENTE, canais carregam em background
                self._ensure_cloner()
                self.show_dashboard(me)
                # Carrega canais em background
                await self.load_channels_background()
            else:
                # Cliente conectado via TCP mas nao autorizado
                self.show_login()
        except Exception as e:
            self.show_error(f"Falha na conexao: {str(e)}")
            self.show_login()

    async def load_channels_background(self):
        """Carrega canais sem bloquear a UI."""
        try:
            self.channels = await self.client.get_channels()
            self.update_channel_dropdowns()
        except Exception as e:
            self.show_error(f"Erro ao carregar canais: {str(e)}")

    def update_channel_dropdowns(self):
        """Atualiza os dropdowns com os canais carregados."""
        options = [
            ft.dropdown.Option(
                key=str(c["id"]),
                text=f"{c['title']} ({c['type']})",
            )
            for c in self.channels
        ]

        if hasattr(self, "source_dd") and self.source_dd:
            self.source_dd.options = options
        if hasattr(self, "dest_dd") and self.dest_dd:
            self.dest_dd.options = list(options)

        # Atualiza o card de estatisticas
        if hasattr(self, "channels_stat") and self.channels_stat:
            self.channels_stat.content.controls[1].controls[0].value = str(len(self.channels))

        # Esconde o texto de carregamento
        if hasattr(self, "channels_loading_text") and self.channels_loading_text:
            self.channels_loading_text.visible = False

        self.page.update()

    def show_loading(self, mensagem):
        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(color=PRIMARY_ACCENT, width=40, height=40),
                        ft.Text(mensagem, color=WHITE, size=16),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
                bgcolor=BG_COLOR,
            )
        )
        self.page.update()

    def show_dashboard(self, user):
        self.page.clean()

        first_name = user.first_name or "Usuario"
        username = user.username or "N/A"
        initial = first_name[0].upper() if first_name else "?"

        # --- Sidebar ---
        sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(icons.SEND_ROUNDED, color=PRIMARY_ACCENT, size=28),
                            ft.Text("DarkoGram", size=22, weight=ft.FontWeight.BOLD, color=WHITE),
                        ], spacing=10),
                        padding=ft.padding.only(bottom=30),
                    ),
                    SelectionTile("Painel", "Visao geral", icons.DASHBOARD_ROUNDED),
                    ft.Container(height=5),
                    SelectionTile("Configuracoes", "Ajustes", icons.SETTINGS_ROUNDED),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Row([
                            ft.CircleAvatar(
                                content=ft.Text(initial, size=16, weight=ft.FontWeight.BOLD),
                                bgcolor=PRIMARY_ACCENT,
                                radius=20,
                            ),
                            ft.Column([
                                ft.Text(first_name, color=WHITE, weight=ft.FontWeight.W_500, size=14),
                                ft.Text(f"@{username}", color=SECONDARY_TEXT, size=11),
                            ], spacing=2),
                        ], spacing=12),
                        padding=ft.padding.only(top=10),
                    ),
                ],
            ),
            width=260,
            bgcolor=SURFACE_COLOR,
            padding=20,
            border_radius=ft.border_radius.only(top_right=20, bottom_right=20),
        )

        # --- Conteudo Principal ---

        self.source_dd = ft.Dropdown(
            text="Canal de Origem",
            width=350,
            options=[],
            on_select=self.on_source_change,
            enable_filter=True,
            enable_search=True,
            bgcolor=SURFACE_COLOR,
            color=WHITE,
            border_radius=10,
            border_color=PRIMARY_ACCENT,
        )

        self.dest_dd = ft.Dropdown(
            text="Canal de Destino",
            width=350,
            options=[],
            on_select=self.on_dest_change,
            enable_filter=True,
            enable_search=True,
            bgcolor=SURFACE_COLOR,
            color=WHITE,
            border_radius=10,
            border_color=PRIMARY_ACCENT,
        )

        self.channels_loading_text = ft.Row([
            ft.ProgressRing(width=16, height=16, color=PRIMARY_ACCENT, stroke_width=2),
            ft.Text("Carregando canais...", size=12, color=SECONDARY_TEXT),
        ], spacing=8)

        self.log_view = ft.ListView(expand=True, spacing=5, auto_scroll=True)

        self.progress_bar = ft.ProgressBar(color=PRIMARY_ACCENT, bgcolor=SURFACE_COLOR, value=0)
        self.progress_text = ft.Text("Pronto", color=SECONDARY_TEXT, size=13)

        self.channels_stat = StatsCard("Canais", "...", icons.LIST_ROUNDED, colors.BLUE_400)

        # Botoes de acao da clonagem
        self.start_btn = PrimaryButton("INICIAR CLONAGEM", self.start_cloning, icon=icons.PLAY_ARROW_ROUNDED, width=220)
        self.pause_btn = PrimaryButton("PAUSAR", self.pause_cloning, icon=icons.PAUSE_ROUNDED, width=150)
        self.pause_btn.visible = False
        self.cancel_btn = PrimaryButton("CANCELAR", self.cancel_cloning, icon=icons.STOP_ROUNDED, width=150)
        self.cancel_btn.visible = False

        self.clone_actions_row = ft.Row([
            self.start_btn,
            self.pause_btn,
            self.cancel_btn,
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

        main_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"Bem-vindo, {first_name}!",
                        size=26,
                        weight=ft.FontWeight.BOLD,
                        color=WHITE,
                    ),
                    ft.Text("Gerencie suas tarefas de clonagem de canais.", size=14, color=SECONDARY_TEXT),
                    ft.Container(height=15),

                    ft.Row([
                        StatsCard("Status", "Conectado", icons.WIFI_ROUNDED, colors.GREEN_400),
                        self.channels_stat,
                        StatsCard("Tarefas", "0", icons.TASK_ROUNDED, colors.ORANGE_400),
                    ], spacing=15),

                    ft.Container(height=20),

                    ft.Container(
                        content=ft.Column([
                            ft.Text("Configuracao de Clonagem", size=18, weight=ft.FontWeight.BOLD, color=WHITE),
                            ft.Container(height=5),
                            self.channels_loading_text,
                            ft.Container(height=10),
                            ft.Row(
                                [
                                    self.source_dd,
                                    ft.Icon(icons.ARROW_FORWARD_ROUNDED, color=SECONDARY_TEXT, size=20),
                                    self.dest_dd,
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=15,
                            ),
                            ft.Container(height=15),
                            self.clone_actions_row,
                        ]),
                        padding=25,
                        bgcolor=SURFACE_COLOR,
                        border_radius=15,
                    ),

                    ft.Container(height=20),

                    ft.Text("Feed de Atividades", size=16, weight=ft.FontWeight.BOLD, color=WHITE),
                    ft.Container(height=5),
                    self.progress_bar,
                    self.progress_text,
                    ft.Container(
                        content=self.log_view,
                        height=180,
                        bgcolor="#141420",
                        border_radius=10,
                        padding=10,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            padding=30,
            expand=True,
        )

        layout = ft.Row(
            [sidebar, main_content],
            expand=True,
            spacing=0,
        )
        self.page.add(layout)
        self.page.update()

    def on_source_change(self, e):
        self.source_channel = e.control.value

    def on_dest_change(self, e):
        self.dest_channel = e.control.value

    def show_error(self, mensagem):
        self.page.snack_bar = ft.SnackBar(
            ft.Text(mensagem, color=WHITE),
            bgcolor=colors.RED_400,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def show_success(self, mensagem):
        self.page.snack_bar = ft.SnackBar(
            ft.Text(mensagem, color=WHITE),
            bgcolor=colors.GREEN_400,
        )
        self.page.snack_bar.open = True
        self.page.update()

    async def log(self, mensagem, nivel="info"):
        self.log_view.controls.append(LogItem(mensagem, nivel))
        self.page.update()

    async def update_progress(self, current, total):
        progress = current / total if total > 0 else 0
        percent = int(progress * 100)
        self.progress_bar.value = progress
        self.progress_text.value = f"Clonando: {current}/{total} mensagens ({percent}%)"
        self.page.update()

    async def start_cloning(self, e):
        if not self.source_channel or not self.dest_channel:
            self.show_error("Selecione o canal de origem e o de destino")
            return

        if self.source_channel == self.dest_channel:
            self.show_error("Origem e destino nao podem ser iguais!")
            return

        self.progress_bar.value = 0
        self.progress_text.value = "Iniciando..."
        self.log_view.controls.clear()

        # Mostrar botoes de pausa/cancelar
        self.start_btn.visible = False
        self.pause_btn.visible = True
        self.cancel_btn.visible = True
        self.page.update()

        self._ensure_cloner()
        await self.log("Inicializando processo de clonagem...", "info")

        await self.cloner.clone_chat(
            int(self.source_channel),
            int(self.dest_channel),
            progress_callback=self.update_progress,
            log_callback=self.log,
        )

        # Restaurar botoes
        self.start_btn.visible = True
        self.pause_btn.visible = False
        self.cancel_btn.visible = False
        self.pause_btn.content.controls[-1].value = "PAUSAR"
        self.page.update()

    async def pause_cloning(self, e):
        if not self.cloner or not self.cloner.is_running:
            return
        if self.cloner.pause_requested:
            self.cloner.resume()
            self.pause_btn.content.controls[-1].value = "PAUSAR"
            self.progress_text.value = "Retomando..."
            await self.log("Clonagem retomada", "info")
        else:
            self.cloner.pause()
            self.pause_btn.content.controls[-1].value = "RETOMAR"
            self.progress_text.value = "Pausado"
            await self.log("Clonagem pausada", "warning")
        self.page.update()

    async def cancel_cloning(self, e):
        if not self.cloner or not self.cloner.is_running:
            return
        self.cloner.stop()
        self.progress_text.value = "Cancelando..."
        await self.log("Cancelando clonagem...", "warning")
        self.page.update()

    # ========================
    # FLUXO DE LOGIN
    # ========================

    def show_login(self):
        """Tela de login para autenticacao no Telegram."""
        self.login_step = "phone"

        self.phone_input = ft.TextField(
            label="Numero de Telefone",
            hint_text="Ex: +5511999999999",
            width=350,
            bgcolor=SURFACE_COLOR,
            color=WHITE,
            border_color=PRIMARY_ACCENT,
            border_radius=10,
        )

        self.code_input = ft.TextField(
            label="Codigo de Verificacao",
            hint_text="Digite o codigo recebido no Telegram",
            width=350,
            bgcolor=SURFACE_COLOR,
            color=WHITE,
            border_color=PRIMARY_ACCENT,
            border_radius=10,
            visible=False,
        )

        self.password_input = ft.TextField(
            label="Senha 2FA",
            hint_text="Senha de verificacao em duas etapas",
            width=350,
            password=True,
            can_reveal_password=True,
            bgcolor=SURFACE_COLOR,
            color=WHITE,
            border_color=PRIMARY_ACCENT,
            border_radius=10,
            visible=False,
        )

        self.login_status = ft.Text("", color=SECONDARY_TEXT, size=13)
        self.login_btn = PrimaryButton("Enviar Codigo", self.handle_login, icon=icons.SEND_ROUNDED, width=220)

        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(icons.SEND_ROUNDED, color=PRIMARY_ACCENT, size=48),
                        ft.Container(height=5),
                        ft.Text("DarkoGram", size=32, weight=ft.FontWeight.BOLD, color=WHITE),
                        ft.Container(height=5),
                        ft.Text("Entre com sua conta do Telegram", size=16, color=SECONDARY_TEXT),
                        ft.Container(height=25),
                        self.phone_input,
                        self.code_input,
                        self.password_input,
                        ft.Container(height=5),
                        self.login_btn,
                        self.login_status,
                        ft.Container(height=15),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Instrucoes:", size=13, weight=ft.FontWeight.BOLD, color=WHITE),
                                ft.Text("1. Digite seu numero com codigo do pais (ex: +55)", size=12, color=SECONDARY_TEXT),
                                ft.Text("2. Voce recebera um codigo no Telegram", size=12, color=SECONDARY_TEXT),
                                ft.Text("3. Se tiver 2FA ativado, sera pedida a senha", size=12, color=SECONDARY_TEXT),
                            ], spacing=4),
                            bgcolor=SURFACE_COLOR,
                            border_radius=10,
                            padding=15,
                            width=350,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                alignment=ft.Alignment(0, 0),
                expand=True,
                bgcolor=BG_COLOR,
            )
        )
        self.page.update()

    async def handle_login(self, e):
        """Gerencia o fluxo de login em etapas."""
        if self.login_step == "phone":
            phone = self.phone_input.value
            if not phone or len(phone) < 8:
                self.show_error("Digite um numero de telefone valido com codigo do pais (ex: +5511999999999)")
                return

            self.login_status.value = "Enviando codigo de verificacao..."
            self.page.update()

            try:
                sent_code = await self.client.app.send_code(phone)
                self.phone_code_hash = sent_code.phone_code_hash
                self.phone_number = phone

                self.login_step = "code"
                self.phone_input.visible = False
                self.code_input.visible = True
                self.login_status.value = "Codigo enviado! Verifique seu Telegram."

                self.login_btn.content.controls[-1].value = "Verificar Codigo"
                self.page.update()

            except Exception as ex:
                logger.error(f"Erro ao enviar codigo: {traceback.format_exc()}")
                self.login_status.value = f"Erro: {str(ex)}"
                self.page.update()

        elif self.login_step == "code":
            code = self.code_input.value
            if not code or len(code) < 3:
                self.show_error("Digite o codigo de verificacao recebido")
                return

            self.login_status.value = "Verificando codigo..."
            self.page.update()

            try:
                result = await self.client.app.sign_in(
                    phone_number=self.phone_number,
                    phone_code_hash=self.phone_code_hash,
                    phone_code=code,
                )

                # sign_in pode retornar User ou TermsOfService
                if isinstance(result, pyrogram_types.TermsOfService):
                    logger.info("Termos de servico recebidos, aceitando automaticamente...")
                    await self.client.app.accept_terms_of_service(result.id)

                # Busca o usuario autenticado
                me = await self.client.app.get_me()
                self.client.is_connected = True
                self.client.is_authorized = True
                logger.info(f"Login realizado com sucesso como {me.first_name}")

                self.show_success("Login realizado com sucesso!")
                self._ensure_cloner()
                try:
                    self.show_dashboard(me)
                except Exception as dash_err:
                    logger.error(f"Erro ao exibir dashboard: {traceback.format_exc()}")
                    self.show_error(f"Erro ao exibir dashboard: {str(dash_err)}")
                await self.load_channels_background()

            except Exception as ex:
                error_msg = str(ex)
                logger.error(f"Erro no sign_in: {traceback.format_exc()}")

                if "SESSION_PASSWORD_NEEDED" in error_msg or "password" in error_msg.lower():
                    self.login_step = "password"
                    self.code_input.visible = False
                    self.password_input.visible = True
                    self.login_status.value = "Sua conta tem 2FA. Digite sua senha."
                    self.login_btn.content.controls[-1].value = "Entrar"
                    self.page.update()
                else:
                    self.login_status.value = f"Erro: {error_msg}"
                    self.page.update()

        elif self.login_step == "password":
            password = self.password_input.value
            if not password:
                self.show_error("Digite sua senha de verificacao em duas etapas")
                return

            self.login_status.value = "Verificando senha..."
            self.page.update()

            try:
                await self.client.app.check_password(password)
                me = await self.client.app.get_me()
                self.client.is_connected = True
                self.client.is_authorized = True
                logger.info(f"Login 2FA realizado com sucesso como {me.first_name}")

                self.show_success("Login realizado com sucesso!")
                self._ensure_cloner()
                try:
                    self.show_dashboard(me)
                except Exception as dash_err:
                    logger.error(f"Erro ao exibir dashboard: {traceback.format_exc()}")
                    self.show_error(f"Erro ao exibir dashboard: {str(dash_err)}")
                await self.load_channels_background()

            except Exception as ex:
                logger.error(f"Erro no 2FA: {traceback.format_exc()}")
                self.login_status.value = f"Senha incorreta: {str(ex)}"
                self.page.update()


def main(page: ft.Page):
    app = DarkoGramApp(page)


if __name__ == "__main__":
    ft.app(target=main)
