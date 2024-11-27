from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widget import Widget
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    RadioButton,
    RadioSet,
    TextArea,
)


def notify_operation_status(app, success: bool, operation: str, message: str) -> None:
    if success:
        app.notify(f"✅ {operation}: {message}")
    else:
        app.notify(f"❌ {operation}: {message}", severity="error")


class TestS2Settings(App):
    AUTO_FOCUS = "Input"

    CSS = """
    #settings-view {
        height: 1fr;
        border: solid $accent;
        padding: 1;
    }

    .controls_row {
        height: auto;
        padding: 1;
        align: left middle;
    }

    #mode_toggle {
        width: 60%;
    }

    #reset_btn, #generate_btn {
        width: 20%;
        margin-left: 1;
    }

    #simple_settings, #advanced_settings {
        margin: 1 0;
        height: 1fr;
        border: solid $accent;
    }

    Input {
        dock: bottom;
        width: 100%;
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()

        with VerticalScroll(id="settings-view"):
            # Top controls
            with Horizontal(id="controls", classes="controls_row"):
                with RadioSet(id="mode_toggle"):
                    yield RadioButton("Simple", id="simple_mode", value=True)
                    yield RadioButton("Advanced", id="advanced_mode")
                yield Button("Reset", id="reset_btn", variant="default")
                yield Button("Generate", id="generate_btn", variant="primary")

            # Simple settings textarea
            yield TextArea.code_editor(
                id="simple_settings",
                language="python",
                theme="monokai",
                soft_wrap=True,
            )

            # Advanced settings textarea (initially disabled)
            yield TextArea.code_editor(
                id="advanced_settings",
                language="python",
                soft_wrap=True,
            )

        yield Input(placeholder="Chat with LLM...", id="chat_input")
        yield Footer()

    @on(RadioSet.Changed, "#mode_toggle")
    def handle_mode_change(self, event: RadioSet.Changed) -> None:
        """Handle mode toggle between Simple and Advanced."""
        advanced_ta = self.query_one("#advanced_settings", TextArea)

        if event.pressed.id == "advanced_mode":
            advanced_ta.set_theme("monokai")  # Enable syntax highlighting
            notify_operation_status(self, True, "Mode", "Advanced enabled")
        else:
            advanced_ta.set_theme("css")  # Disable syntax highlighting
            notify_operation_status(self, True, "Mode", "Simple enabled")

    @on(Button.Pressed, "#reset_btn")
    def handle_reset(self) -> None:
        """Handle reset button press."""
        simple_ta = self.query_one("#simple_settings", TextArea)
        advanced_ta = self.query_one("#advanced_settings", TextArea)
        simple_ta.clear()
        advanced_ta.clear()
        notify_operation_status(self, True, "Reset", "Settings cleared")

    @on(Button.Pressed, "#generate_btn")
    def handle_generate(self) -> None:
        """Handle generate button press."""
        simple_ta = self.query_one("#simple_settings", TextArea)
        advanced_ta = self.query_one("#advanced_settings", TextArea)
        # TODO: Implement generation logic
        notify_operation_status(self, True, "Generate", "Settings generated")

    @on(Input.Submitted)
    async def on_input(self, event: Input.Submitted) -> None:
        """Handle chat input submission."""
        event.input.clear()
        notify_operation_status(self, True, "Chat", "Message sent to LLM")


if __name__ == "__main__":
    app = TestS2Settings()
    app.run()
