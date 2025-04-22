"""
Reaction Test Game

Made as Michael Moshchuk's 2025 AP CSP Create Performance Task, this is a
simple Qt implementation of a reaction test game. After a random wait period,
a central button turns green and the player must click it as quickly as possible.
The program times their reaction and displays the result.
"""

import sys
import random
import time
import enum
import os
import PySide6.QtWidgets
import PySide6.QtCore
import PySide6.QtGui
import PySide6.QtSvgWidgets


# =============================================================================
# PARAMETERS
# =============================================================================
# --- UI Proportions ---
INSTRUCTION_BOX_WIDTH: float = 0.75  # vw (box width as fraction of window width)
INSTRUCTION_BOX_HEIGHT: float = 0.15  # vh (box height as fraction of window height)
INSTRUCTION_RADIUS: int = 18  # px
SPACE_INDICATOR_WIDTH: float = 0.35  # vw
SPACE_INDICATOR_HEIGHT: float = 0.15  # vh
SPACE_INDICATOR_BOTTOM_MARGIN: float = 0.08  # vh
SPACE_RADIUS: int = 10  # px
MIN_FONT_SIZE: int = 8  # px
TOP_BAR_HEIGHT: float = 0.10  # vh
TROPHY_PADDING: float = 0.05  # max(vw, vh)

# min(% of space indicator width, % of space indicator height)
SPACE_BORDER: int = 5

# Digits of precision for stretch calculations
# We need to pick a value here since stretch factors have to be integers
STRETCH_PRECISION: int = 3

# ms for which the trophy is shown
TROPHY_DURATION: int = 1000  # ms


# --- Centralized Color Scheme ---
def hsl(h: int, s: int, l: int) -> PySide6.QtGui.QColor:
    """Convenience alias for improved readability"""
    return PySide6.QtGui.QColor.fromHsl(h, s, l)


class Colors:
    """
    Centralized color scheme.
    Using HSL rather than RGB because it's more intuitive.
    """

    # Instruction box defaults
    INSTRUCTION_FILL: PySide6.QtGui.QColor = hsl(210, 160, 140)  # vibrant blue
    INSTRUCTION_TEXT: PySide6.QtGui.QColor = hsl(0, 0, 255)  # white

    # Space indicator
    SPACE_FILL: PySide6.QtGui.QColor = hsl(210, 40, 230)  # light blue‑gray
    SPACE_PRESSED: PySide6.QtGui.QColor = hsl(210, 100, 180)  # dark blue
    SPACE_TEXT: PySide6.QtGui.QColor = hsl(0, 0, 30)  # near‑black
    SPACE_BORDER: PySide6.QtGui.QColor = hsl(210, 80, 160)  # blue border

    # Status modifiers for instruction box
    WAIT: PySide6.QtGui.QColor = hsl(39, 240, 180)  # warm orange/yellow
    GO: PySide6.QtGui.QColor = hsl(120, 200, 125)  # vibrant green
    ERROR: PySide6.QtGui.QColor = hsl(0, 240, 160)  # vibrant red

    # Result fill set to same as GO, but easy to change if desired
    RESULT_FILL: PySide6.QtGui.QColor = GO

    # Top bar
    TOP_BAR: PySide6.QtGui.QColor = hsl(210, 80, 160)  # blue
    TOP_BAR_TEXT: PySide6.QtGui.QColor = hsl(0, 0, 255)  # white


# =============================================================================
# UTILS
# =============================================================================


def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource,
    used for ensuring functionality in both dev and PyInstaller use cases
    (This is for the AppImage build which allows
    my program to function as a desktop application)
    """
    default_base_path: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    # _MEIPASS will be defined if the program is running via PyInstaller
    base_path: str = getattr(sys, '_MEIPASS', default_base_path)

    return os.path.join(base_path, "assets", relative_path)


class GameState(enum.Enum):
    """Represents the finite set of game states"""

    READY = enum.auto()  # Initial state, waiting for player to start
    WAITING = enum.auto()  # Random wait period before GO signal
    REACT = enum.auto()  # GO signal, player should react
    RESULT = enum.auto()  # Showing reaction time result
    TOO_EARLY = enum.auto()  # Player pressed before the GO signal


# =============================================================================
# MAIN WINDOW
# =============================================================================


# Use a class for inheritance from QMainWindow
class ReactionGame(PySide6.QtWidgets.QMainWindow):
    # --- Class Attributes (declared here for type hinting) ---
    state: GameState
    start_time: Optional[float]
    timer: PySide6.QtCore.QTimer
    best_time: Optional[float]
    trophy_timer: PySide6.QtCore.QTimer
    trophy_animation: PySide6.QtCore.QPropertyAnimation

    instruction_box: PySide6.QtWidgets.QLabel
    space_indicator: PySide6.QtWidgets.QLabel
    top_bar: PySide6.QtWidgets.QWidget
    best_time_label: PySide6.QtWidgets.QLabel
    trophy: PySide6.QtSvgWidgets.QSvgWidget
    trophy_opacity_effect: PySide6.QtWidgets.QGraphicsOpacityEffect
    trophy_animation_group: None | PySide6.QtCore.QSequentialAnimationGroup

    def __init__(self):
        # Initialize parent QMainWindow class - required for Qt functionality
        super().__init__()
        # Set window icon and properties
        self.setWindowTitle("ReactionTimer")
        self.setGeometry(100, 100, 400, 300)

        # Credit: Icon image created by OpenAI's GPT-4o
        app_icon_path: str = resource_path("app_icon.png")
        app_icon: PySide6.QtGui.QIcon = PySide6.QtGui.QIcon(app_icon_path)
        self.setWindowIcon(app_icon)

        font: PySide6.QtGui.QFont = PySide6.QtGui.QFont()
        font.setFamily("Arial")
        self.setFont(font)
        self.initGame()
        self.initUI()

    def _update_font_size(self, label_widget: PySide6.QtWidgets.QLabel) -> None:
        """Recalculates and sets the font size for a label based on its current text and size."""
        width: int = label_widget.width()
        height: int = label_widget.height()

        font: PySide6.QtGui.QFont = label_widget.font()
        font_size: int = MIN_FONT_SIZE
        # Calculate font size
        while True:
            font.setPointSize(font_size + 1)

            metrics: PySide6.QtGui.QFontMetrics = PySide6.QtGui.QFontMetrics(font)
            text_width: int = metrics.horizontalAdvance(label_widget.text())
            text_height: int = metrics.height()

            # Calculate font size based on both dimensions to ensure it's readable
            # 0.9 gives slight breathing room
            if text_width > width * 0.9 or text_height > height * 0.9:
                break
            font_size += 1
        font.setPointSize(font_size)
        label_widget.setFont(font)

    def initUI(self) -> None:
        """Initialize the main UI window"""
        # Allow resizing but ensure the size is at least reasonable
        self.setMinimumSize(400, 400)

        # In Qt, a main window requires a central widget that everything else
        # is added to
        central_widget: PySide6.QtWidgets.QWidget = PySide6.QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout: PySide6.QtWidgets.QVBoxLayout = PySide6.QtWidgets.QVBoxLayout(
            central_widget
        )
        layout.setContentsMargins(0, 0, 0, 0)  # Remove default margins
        layout.setSpacing(0)  # Spacing complexifies stretch calculations

        # --- Widget 1: Top Bar ---
        self.top_bar = PySide6.QtWidgets.QWidget()
        self.top_bar.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                          stop:0 {Colors.TOP_BAR.name()}, stop:1 {PySide6.QtGui.QColor.darker(Colors.TOP_BAR, 120).name()});
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            }}
        """)

        # --- Top Bar Contents ---
        top_layout = PySide6.QtWidgets.QHBoxLayout(self.top_bar)

        # Remove default margins from top and bottom
        top_layout.setContentsMargins(10, 0, 10, 0)
        top_layout.addStretch(1)  # Pushes the label to the right

        self.best_time_label = PySide6.QtWidgets.QLabel()
        self.best_time_label.setStyleSheet(
            f"color: {Colors.TOP_BAR_TEXT.name()}; font-weight: bold;"
            # TODO: Add padding if needed: "padding-right: 5px;"
        )
        self.best_time_label.setAlignment(
            PySide6.QtCore.Qt.AlignmentFlag.AlignRight
            | PySide6.QtCore.Qt.AlignmentFlag.AlignVCenter
        )  # Use bitwise OR to combine alignment flags

        # Let the label expand horizontally within the layout
        self.best_time_label.setSizePolicy(
            PySide6.QtWidgets.QSizePolicy.Policy.MinimumExpanding,
            PySide6.QtWidgets.QSizePolicy.Policy.Preferred,
        )

        top_layout.addWidget(self.best_time_label)

        self.top_bar.hide()
        layout.addWidget(self.top_bar)  # Add to main layout

        # Calculate stretch factor so that the instruction box is centered vertically
        layout.addStretch(
            int((0.5 - INSTRUCTION_BOX_HEIGHT / 2.0) * 10**STRETCH_PRECISION)
        )  # Pushes instruction box down

        # --- Trophy ---
        # Credit: Trophy image by @monsterbraingames via OpenClipart
        # (https://openclipart.org/artist/monsterbraingames)
        trophy_path = resource_path("trophy.svg")
        self.trophy = PySide6.QtSvgWidgets.QSvgWidget(trophy_path)
        self.trophy.hide()
        # An individual widget has no opacity property, so we add a controlable effect on top of it
        self.trophy_opacity_effect = PySide6.QtWidgets.QGraphicsOpacityEffect(
            self.trophy
        )
        self.trophy.setGraphicsEffect(self.trophy_opacity_effect)

        layout.addWidget(
            self.trophy, alignment=PySide6.QtCore.Qt.AlignmentFlag.AlignCenter
        )

        # --- Widget 2: Instruction Box ---
        # No parent needed because we're adding to layout
        self.instruction_box = PySide6.QtWidgets.QLabel()
        self.instruction_box.setSizePolicy(
            PySide6.QtWidgets.QSizePolicy.Policy.Expanding,
            PySide6.QtWidgets.QSizePolicy.Policy.Expanding,
        )

        # Add a shadow effect to the instruction box for a little flair
        shadow = PySide6.QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(PySide6.QtGui.QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        self.instruction_box.setGraphicsEffect(shadow)

        self.instruction_box.setStyleSheet(f"""
            QLabel {{
                background-color: {Colors.INSTRUCTION_FILL.name()};
                border-radius: {INSTRUCTION_RADIUS}px;
                color: {Colors.INSTRUCTION_TEXT.name()};
                font-weight: bold;
            }}
            QLabel[game_state="waiting"] {{
                background-color: {Colors.WAIT.name()};
            }}
            QLabel[game_state="react"] {{
                background-color: {Colors.GO.name()};
            }}
            QLabel[game_state="result"] {{
                background-color: {Colors.RESULT_FILL.name()};
            }}
            QLabel[game_state="too_early"] {{
                background-color: {Colors.ERROR.name()};
            }}
        """)
        self.instruction_box.setText("Press SPACE to start!")
        self.instruction_box.setAlignment(PySide6.QtCore.Qt.AlignmentFlag.AlignCenter)
        # Stretched to full width by default, but since we update its size manually
        # the alignment needs to be set
        layout.addWidget(
            self.instruction_box, alignment=PySide6.QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        # Second stretch calculation
        layout.addStretch(
            int(
                (
                    0.5
                    - INSTRUCTION_BOX_HEIGHT / 2.0
                    - SPACE_INDICATOR_HEIGHT
                    - SPACE_INDICATOR_BOTTOM_MARGIN
                )
                * 10**STRETCH_PRECISION
            )
        )

        # --- Widget 3: Space Indicator ---
        # Create WITHOUT central_widget parent
        self.space_indicator = PySide6.QtWidgets.QLabel("SPACE")
        # Let layout handle size, set preferred size via font/content
        self.space_indicator.setSizePolicy(
            PySide6.QtWidgets.QSizePolicy.Policy.Preferred,  # Width preferred based on content
            PySide6.QtWidgets.QSizePolicy.Policy.Preferred,  # Height preferred based on content
        )

        # Add shadow effect to the space button
        button_shadow = PySide6.QtWidgets.QGraphicsDropShadowEffect()
        button_shadow.setBlurRadius(15)
        button_shadow.setColor(PySide6.QtGui.QColor(0, 0, 0, 60))
        button_shadow.setOffset(0, 4)
        self.space_indicator.setGraphicsEffect(button_shadow)

        # Initial styleSheet is set by resizeEvent

        self.space_indicator.setAlignment(PySide6.QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(
            self.space_indicator, alignment=PySide6.QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        layout.addStretch(int(SPACE_INDICATOR_BOTTOM_MARGIN * 10**STRETCH_PRECISION))

        self.resizeEvent(None)  # Set initial size and position

    def initGame(self) -> None:
        """Initialize game state and variables"""
        self.game_state = GameState.READY
        self.best_time = float("inf")
        self.start_time = 0.0
        self.reaction_time: float = 0.0
        self.wait_start_time: float = 0.0
        self.random_wait_time: float = 0.0
        self.wait_timer = PySide6.QtCore.QTimer()
        self.wait_timer.timeout.connect(self.check_wait_time)
        self.trophy_animation_group = None

    def resizeEvent(self, event: PySide6.QtGui.QResizeEvent) -> None:
        """Handle window resize events to maintain proportional sizing"""
        window_width: int = self.width()
        window_height: int = self.height()
        layout: PySide6.QtWidgets.QVBoxLayout = self.centralWidget().layout()
        top_layout: PySide6.QtWidgets.QHBoxLayout = self.top_bar.layout()

        # --- Top Bar --
        # The bar itself
        self.top_bar.setFixedHeight(int(window_height * TOP_BAR_HEIGHT))
        # The best time label container
        container_height = (
            self.top_bar.height()
            - top_layout.contentsMargins().top()
            - top_layout.contentsMargins().bottom()
        )
        # Calculate available width: total width - margins - trophy width - spacing around stretch
        available_width = (
            self.top_bar.width()
            - top_layout.contentsMargins().left()
            - top_layout.contentsMargins().right()
            - top_layout.spacing() * 2
        )
        self.best_time_label.setFixedSize(available_width, container_height)
        # Finally update the font size
        self._update_font_size(self.best_time_label)

        # Layout might have adjusted sizes slightly, so throughout this function
        # we use measured values rather than the calculated ones

        # --- Instruction Box ---
        self.instruction_box.setFixedSize(
            int(window_width * INSTRUCTION_BOX_WIDTH),
            int(window_height * INSTRUCTION_BOX_HEIGHT),
        )
        self._update_font_size(self.instruction_box)

        # --- Space Indicator ---
        space_width = int(window_width * SPACE_INDICATOR_WIDTH)
        space_height = int(window_height * SPACE_INDICATOR_HEIGHT)
        self.space_indicator.setFixedSize(space_width, space_height)

        # Calculate dynamic border width based on the size of the space indicator
        # Use the specified percentage of the minimum dimension
        dynamic_border_width = int(min(space_width, space_height) * SPACE_BORDER / 100)
        # Ensure border is at least 1px
        dynamic_border_width = max(1, dynamic_border_width)

        # Set all the styling here since we didn't set it earlier
        self.space_indicator.setStyleSheet(f"""
            QLabel {{ /* Default state */
                background: {Colors.SPACE_FILL.name()};
                border: {dynamic_border_width}px solid {Colors.SPACE_BORDER.name()};
                border-radius: {SPACE_RADIUS}px;
                color: {Colors.SPACE_TEXT.name()};
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QLabel[pressed="true"] {{
                background: {Colors.SPACE_PRESSED.name()};
                border-color: {Colors.SPACE_PRESSED.name()};
                color: {Colors.INSTRUCTION_TEXT.name()};
            }}
        """)

        self._update_font_size(self.space_indicator)

        # --- Restart Trophy Animation ---
        # While it might be possible to adjust the ongoing animation, it's much simpler and more reliable to stop and restart
        if (
            self.trophy_animation_group is not None
            and self.trophy_animation_group.state()
            == PySide6.QtCore.QAbstractAnimation.State.Running
        ):
            self.animate_trophy()  # Handles both stopping and starting

        # This resizeEvent function overrides the existing method, so we add a call to the
        # parent implementation at the end
        super().resizeEvent(event)

    def animate_trophy(self) -> None:
        """Animated trophy appearance (It's the little things that make a difference)"""
        # --- Prepare ---
        # Stop any existing animation group *before* creating a new one
        if self.trophy_animation_group is not None:
            # Check state before stopping to avoid issues if already stopped
            if (
                self.trophy_animation_group.state()
                != PySide6.QtCore.QAbstractAnimation.State.Stopped
            ):
                self.trophy_animation_group.stop()
            self.trophy_animation_group = None

        animation_sequence: PySide6.QtCore.QSequentialAnimationGroup = (
            PySide6.QtCore.QSequentialAnimationGroup(self)
        )

        # --- Calculate Size ---
        top_bar_height: int = (
            self.top_bar.height() if self.top_bar.isVisible() else 0
        )
        # The top bar *should* be visible, but check anyway for future proofing
        instruction_box_y: int = self.instruction_box.y()
        available_height: int = instruction_box_y - top_bar_height
        padding_factor: float = 1.0 - TROPHY_PADDING
        max_height: int = int(available_height * padding_factor)
        max_width: int = int(self.width() * padding_factor)

        target_size = min(max_height, max_width)

        # --- Animate ---
        grow_animation: PySide6.QtCore.QPropertyAnimation = (
            PySide6.QtCore.QPropertyAnimation(self.trophy, b"minimumSize")
        )
        grow_animation.setDuration(TROPHY_DURATION // 2)
        grow_animation.setStartValue(PySide6.QtCore.QSize(0, 0))
        grow_animation.setEndValue(PySide6.QtCore.QSize(target_size, target_size))
        grow_animation.setEasingCurve(PySide6.QtCore.QEasingCurve.Type.OutCubic)

        animation_sequence.addAnimation(grow_animation)

        # Create a parallel group for fade and shrink so that they can run simultaneously
        shrink_fade_group: PySide6.QtCore.QParallelAnimationGroup = (
            PySide6.QtCore.QParallelAnimationGroup()
        )

        # Shrink
        shrink_animation: PySide6.QtCore.QPropertyAnimation = (
            PySide6.QtCore.QPropertyAnimation(self.trophy, b"minimumSize")
        )
        shrink_animation.setDuration(TROPHY_DURATION // 2)
        shrink_animation.setStartValue(PySide6.QtCore.QSize(target_size, target_size))
        shrink_animation.setEndValue(PySide6.QtCore.QSize(0, 0))
        shrink_animation.setEasingCurve(PySide6.QtCore.QEasingCurve.Type.InCubic)

        # Fade
        fade_animation: PySide6.QtCore.QPropertyAnimation = (
            PySide6.QtCore.QPropertyAnimation(
                self.trophy_opacity_effect, b"opacity"
            )
        )
        fade_animation.setDuration(TROPHY_DURATION // 2)
        fade_animation.setStartValue(1.0)
        fade_animation.setEndValue(0.0)
        fade_animation.setEasingCurve(PySide6.QtCore.QEasingCurve.Type.InCubic)

        shrink_fade_group.addAnimation(shrink_animation)
        shrink_fade_group.addAnimation(fade_animation)
        animation_sequence.addAnimation(shrink_fade_group)

        # --- Begin ---
        # Set trophy's initial state
        self.trophy.setFixedSize(0, 0)
        self.trophy_opacity_effect.setOpacity(1.0)
        self.trophy.show()

        # Store and start the animation
        self.trophy_animation_group = animation_sequence
        self.trophy_animation_group.start()

    def keyPressEvent(self, event: PySide6.QtGui.QKeyEvent) -> None:
        """Handle keyboard events"""
        # Ignore auto-repeat events from holding the key down
        if event.key() == PySide6.QtCore.Qt.Key.Key_Space and not event.isAutoRepeat():
            self.space_indicator.setProperty("pressed", True)
            # Force style update
            self.space_indicator.style().unpolish(self.space_indicator)
            self.space_indicator.style().polish(self.space_indicator)

            self.handle_space_press()

    def keyReleaseEvent(self, event: PySide6.QtGui.QKeyEvent) -> None:
        """Handle keyboard release events"""
        if event.key() == PySide6.QtCore.Qt.Key.Key_Space:
            self.space_indicator.setProperty("pressed", False)
            self.space_indicator.style().unpolish(self.space_indicator)
            self.space_indicator.style().polish(self.space_indicator)

    def handle_space_press(self) -> None:
        """Handle space bar press based on game state"""
        if self.game_state == GameState.READY:
            self.instruction_box.setProperty("game_state", "waiting")
            self.start_waiting()
        elif self.game_state == GameState.WAITING:
            self.instruction_box.setProperty("game_state", "too_early")
            self.too_early()
        elif self.game_state == GameState.REACT:
            self.instruction_box.setProperty("game_state", "result")
            self.show_result()
        elif self.game_state in [GameState.RESULT, GameState.TOO_EARLY]:
            self.instruction_box.setProperty("game_state", "waiting")
            self.start_waiting()
        # Update font size after game state text update
        self._update_font_size(self.instruction_box)
        self.instruction_box.style().unpolish(self.instruction_box)
        self.instruction_box.style().polish(self.instruction_box)

    def start_waiting(self) -> None:
        """Start the waiting period"""
        self.game_state = GameState.WAITING
        self.wait_start_time = time.time()
        self.random_wait_time = random.uniform(2.0, 5.0)
        self.instruction_box.setText("Wait for it...")
        self.wait_timer.start(10)  # Check every 10ms

    def too_early(self) -> None:
        """Handle early button press"""
        self.game_state = GameState.TOO_EARLY
        self.wait_timer.stop()
        self.instruction_box.setText("Too eager! Try again.\nPress SPACE to continue")

        # Shake animation to provide visual feedback for error
        animation: PySide6.QtCore.QPropertyAnimation = (
            PySide6.QtCore.QPropertyAnimation(self.instruction_box, b"pos")
        )
        animation.setDuration(200)
        start_pos: PySide6.QtCore.QPoint = self.instruction_box.pos()

        # Create keyframes for shake effect
        animation.setKeyValueAt(0, start_pos)
        animation.setKeyValueAt(0.2, start_pos + PySide6.QtCore.QPoint(5, 0))
        animation.setKeyValueAt(0.4, start_pos + PySide6.QtCore.QPoint(-5, 0))
        animation.setKeyValueAt(0.6, start_pos + PySide6.QtCore.QPoint(3, 0))
        animation.setKeyValueAt(0.8, start_pos + PySide6.QtCore.QPoint(-3, 0))
        animation.setKeyValueAt(1, start_pos)

        animation.start()

    def show_result(self) -> None:
        """Show reaction time result"""
        self.reaction_time = time.time() - self.start_time
        if self.reaction_time < self.best_time:
            self.best_time = self.reaction_time
            self.best_time_label.setText(f"BEST: {self.best_time:.3f} s")
            if not self.top_bar.isVisible():
                # Recalculate 2nd stretch factor since top bar is now taking up space
                layout = self.centralWidget().layout()
                new_stretch = layout.stretch(1) - int(
                    TOP_BAR_HEIGHT * 10**STRETCH_PRECISION
                )
                layout.setStretch(1, new_stretch)
                self.top_bar.show()
            self.animate_trophy()
        if self.reaction_time < 0.05:
            # Little easter egg
            result_text = f"WOW, {self.reaction_time:.3f} seconds!\nAre you a bot?! Press SPACE to try again..."
        else:
            result_text = (
                f"Your time: {self.reaction_time:.3f} seconds\nPress SPACE to try again"
            )

        self.game_state = GameState.RESULT
        self.instruction_box.setText(result_text)
        # Trigger resize event due to textual content change
        self.resizeEvent(None)

    def check_wait_time(self) -> None:
        """Check if waiting period is over"""
        if time.time() - self.wait_start_time >= self.random_wait_time:
            self.wait_timer.stop()
            self.game_state = GameState.REACT
            self.start_time = time.time()
            self.instruction_box.setText("GO!!!")
            self.instruction_box.setProperty("game_state", "react")
            self._update_font_size(self.instruction_box)
            # Changes don't take effect unless we unpolish and repolish
            self.instruction_box.style().unpolish(self.instruction_box)
            self.instruction_box.style().polish(self.instruction_box)


# =============================================================================
# PROGRAM EXECUTION
# =============================================================================


def main() -> None:
    app: PySide6.QtWidgets.QApplication = PySide6.QtWidgets.QApplication(sys.argv)
    game: ReactionGame = ReactionGame()
    game.show()
    sys.exit(app.exec())


# Allows my code to be imported as a module without inherently running the game, good practice
if __name__ == "__main__":
    main()
