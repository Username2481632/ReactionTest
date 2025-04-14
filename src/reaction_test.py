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
import os # Import os module
import PySide6.QtWidgets
import PySide6.QtCore
import PySide6.QtGui
import PySide6.QtSvgWidgets

# ===============================================================================
# Asset Path Helper
# ===============================================================================
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # Assets are expected to be in an 'assets' subdirectory relative to this
        base_path = sys._MEIPASS
    except Exception:
        # Not running as a PyInstaller bundle, assume standard structure
        # Go up one level from src/ to project root, then into assets/
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Always join with 'assets' subdirectory name
    return os.path.join(base_path, 'assets', relative_path)

# ===============================================================================
# PARAMETERS
# ===============================================================================
# UI Proportions
INSTRUCTION_BOX_WIDTH = 0.75 # Box width as fraction of window width
INSTRUCTION_BOX_HEIGHT = 0.15 # Box height as fraction of window height
INSTRUCTION_RADIUS = 18 # px
SPACE_INDICATOR_WIDTH = 0.35 # vw
SPACE_INDICATOR_HEIGHT = 0.15 # vh
SPACE_INDICATOR_BOTTOM_MARGIN = 0.08 # vh
SPACE_RADIUS = 10 # px
MIN_FONT_SIZE = 8 # px
TOP_BAR_HEIGHT = 0.10 # vh
TROPHY_HEIGHT = 0.85 # %
SPACE_BORDER = 5 # %, min of width and height
STRETCH_PRECISION = 1000 # digits of precision for stretch calculations

class Colors:
    """
    Centralized color scheme for the entire project, using HSL rather than RGB
    because it's more intuitive to work with
    """
    INSTRUCTION_FILL = PySide6.QtGui.QColor.fromHsl(210, 160, 140)     # Vibrant blue
    INSTRUCTION_TEXT = PySide6.QtGui.QColor.fromHsl(0, 0, 255) # white
    SPACE_FILL = PySide6.QtGui.QColor.fromHsl(210, 40, 230) # light blue-gray
    SPACE_PRESSED = PySide6.QtGui.QColor.fromHsl(210, 100, 180) # dark blue
    SPACE_TEXT = PySide6.QtGui.QColor.fromHsl(0, 0, 30) # near black
    SPACE_BORDER = PySide6.QtGui.QColor.fromHsl(210, 80, 160) # blue border
    WAIT = PySide6.QtGui.QColor.fromHsl(39, 240, 180) # warm orange/yellow
    GO = PySide6.QtGui.QColor.fromHsl(120, 200, 125) # vibrant green
    ERROR = PySide6.QtGui.QColor.fromHsl(0, 240, 160) # vibrant red
    RESULT_FILL = PySide6.QtGui.QColor.fromHsl(140, 180, 150) # soft green
    TOP_BAR = PySide6.QtGui.QColor.fromHsl(210, 80, 160) # blue
    TOP_BAR_TEXT = PySide6.QtGui.QColor.fromHsl(0, 0, 255) # white

# ===============================================================================
# UTILS
# ===============================================================================
def calculate_font_size(box, width, height):
    """Calculate font size for auto-fitting text within a box"""
    font = box.font()
    
    size = MIN_FONT_SIZE
    while True:
        font.setPointSize(size + 1)
        
        metrics = PySide6.QtGui.QFontMetrics(font)
        text_width = metrics.horizontalAdvance(box.text())
        text_height = metrics.height()

        # Calculate font size based on both dimensions to ensure it's readable
        # 0.9 and 0.8 give slight breathing room
        if text_width > width * 0.9 or text_height > height * 0.8: 
            return size
        size += 1

class GameState(enum.Enum):
    """Represents the finite set of game states"""
    READY = enum.auto()      # Initial state, waiting for player to start
    WAITING = enum.auto()    # Random wait period before GO signal
    REACT = enum.auto()      # GO signal, player should react
    RESULT = enum.auto()     # Showing reaction time result
    TOO_EARLY = enum.auto()  # Player pressed before the GO signal

# Use a class for inheritance from QMainWindow
class ReactionGame(PySide6.QtWidgets.QMainWindow): 
    def __init__(self):
        # Initialize parent QMainWindow class - required for Qt functionality
        super().__init__() 
        # Set window icon and properties
        self.setWindowTitle('ReactionTest')
        
        # Credit: Icon image created by OpenAI's GPT-4o
        # Use resource_path to find the icon
        app_icon_path = resource_path("app_icon.png")
        app_icon = PySide6.QtGui.QIcon(app_icon_path)
        self.setWindowIcon(app_icon)
        
        font = PySide6.QtGui.QFont()
        font.setFamily("Arial")
        self.setFont(font)
        self.initUI()
        self.initGame()
        
    def _update_font_size(self, label_widget):
        """Recalculates and sets the font size for a label based on its current text and size."""
        width = label_widget.width()
        height = label_widget.height()
        font_size = calculate_font_size(
            label_widget, width, height
        )
        font = label_widget.font()
        font.setPointSize(font_size)
        label_widget.setFont(font)
        
    def initUI(self):
        """Initialize the main UI window"""
        # Allow resizing but ensure the size is at least reasonable
        self.setMinimumSize(400, 400)  
        
        # In Qt, a main window requires a central widget that everything else
        # is added to
        central_widget = PySide6.QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = PySide6.QtWidgets.QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0) # Remove default margins
        layout.setSpacing(0) # Spacing complexifies stretch calculations

        # --- Widget 1: Top Bar ---
        self.top_bar = PySide6.QtWidgets.QWidget()
        # This is required for palette to take effect
        self.top_bar.setAutoFillBackground(True) 
        palette = self.top_bar.palette()
        palette.setColor(PySide6.QtGui.QPalette.ColorRole.Window, Colors.TOP_BAR)
        self.top_bar.setPalette(palette)

        # --- Top Bar Contents ---
        # Create a sub-layout INSIDE top_bar
        top_layout = PySide6.QtWidgets.QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(10, 0, 10, 0) # Remove default margins
        # Credit: Trophy image by @monsterbraingames via OpenClipart
        # (https://openclipart.org/artist/monsterbraingames)
        # Use resource_path to find the trophy svg
        trophy_path = resource_path('trophy.svg')
        self.trophy = PySide6.QtSvgWidgets.QSvgWidget(trophy_path)
        top_layout.addWidget(self.trophy)
        top_layout.addStretch(1)
        self.best_time_label = PySide6.QtWidgets.QLabel()
        self.best_time_label.setWordWrap(True) # Allow text wrapping
        self.best_time_label.setStyleSheet(
            f'color: {Colors.TOP_BAR_TEXT.name()}; font-weight: bold'
        )

        self.best_time_label.setAlignment(PySide6.QtCore.Qt.AlignmentFlag.AlignRight | PySide6.QtCore.Qt.AlignmentFlag.AlignVCenter)
        # Create a container for the best time label to ensure text doesn't
        # overflow into the trophy
        self.best_time_container = PySide6.QtWidgets.QWidget()
        best_time_layout = PySide6.QtWidgets.QVBoxLayout(self.best_time_container)
        best_time_layout.setContentsMargins(0, 0, 0, 0)
        best_time_layout.addWidget(self.best_time_label)
        top_layout.addWidget(self.best_time_container)

        self.top_bar.hide()
        layout.addWidget(self.top_bar)
        # Calculate stretch factor so that the top bar is centered vertically
        layout.addStretch(int((0.5-INSTRUCTION_BOX_HEIGHT/2.0)*STRETCH_PRECISION)) # Pushes instruction box down

        # --- Widget 2: Instruction Box ---
        # No parent needed because we're adding to layout
        self.instruction_box = PySide6.QtWidgets.QLabel()
        self.instruction_box.setSizePolicy(
            PySide6.QtWidgets.QSizePolicy.Policy.Expanding,
            PySide6.QtWidgets.QSizePolicy.Policy.Expanding
        )
        
        # Add a shadow effect to the instruction box for a little flair
        shadow = PySide6.QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(PySide6.QtGui.QColor(0, 0, 0, 50))
        shadow.setOffset(0, 5)
        self.instruction_box.setGraphicsEffect(shadow)
        
        self.instruction_box.setStyleSheet(f'''
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
        ''')
        self.instruction_box.setText("Press SPACE to start!")
        self.instruction_box.setAlignment(PySide6.QtCore.Qt.AlignmentFlag.AlignCenter)
        # Stretched to full width by default, but since we update its size manually
        # the alignment needs to be set
        layout.addWidget(self.instruction_box, alignment=PySide6.QtCore.Qt.AlignmentFlag.AlignHCenter)
        # Second stretch calculation
        layout.addStretch(int((0.5-INSTRUCTION_BOX_HEIGHT/2.0-SPACE_INDICATOR_HEIGHT-SPACE_INDICATOR_BOTTOM_MARGIN)*STRETCH_PRECISION))

        # --- Widget 3: Space Indicator ---
         # Create WITHOUT central_widget parent
        self.space_indicator = PySide6.QtWidgets.QLabel('SPACE')
        # Let layout handle size, set preferred size via font/content
        self.space_indicator.setSizePolicy(
            PySide6.QtWidgets.QSizePolicy.Policy.Preferred, # Width preferred based on content
            PySide6.QtWidgets.QSizePolicy.Policy.Preferred  # Height preferred based on content
        )
        
        # Add shadow effect to the space button
        button_shadow = PySide6.QtWidgets.QGraphicsDropShadowEffect()
        button_shadow.setBlurRadius(15)
        button_shadow.setColor(PySide6.QtGui.QColor(0, 0, 0, 60))
        button_shadow.setOffset(0, 4)
        self.space_indicator.setGraphicsEffect(button_shadow)
        
        # Initial styleSheet is set by resizeEvent
        
        self.space_indicator.setAlignment(
            PySide6.QtCore.Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(self.space_indicator, alignment=PySide6.QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(int(SPACE_INDICATOR_BOTTOM_MARGIN*STRETCH_PRECISION))

        self.resizeEvent(None) # Set initial size and position
        
    def initGame(self):
        """Initialize game variables"""
        self.game_state = GameState.READY
        self.best_time = float('inf')
        self.start_time = 0
        self.reaction_time = 0
        self.wait_start_time = 0
        self.random_wait_time = 0
        self.timer = PySide6.QtCore.QTimer()
        self.timer.timeout.connect(self.check_wait_time)
        
    def resizeEvent(self, event):
        """Handle window resize events to maintain proportional sizing"""
        window_width = self.width()
        window_height = self.height()
        layout = self.centralWidget().layout()
        top_layout = self.top_bar.layout()

        # --- Top Bar --
        # The bar itself
        self.top_bar.setFixedHeight(int(window_height * TOP_BAR_HEIGHT))
        # The trophy
        trophy_size = int(self.top_bar.height() * TROPHY_HEIGHT)
        self.trophy.setFixedSize(trophy_size, trophy_size)
        # The best time label container
        container_height = self.top_bar.height() - top_layout.contentsMargins().top() - top_layout.contentsMargins().bottom()
        # Calculate available width: total width - margins - trophy width - spacing around stretch
        available_width = self.top_bar.width() - top_layout.contentsMargins().left() - top_layout.contentsMargins().right() - trophy_size - top_layout.spacing() * 2
        # Ensure width is not negative
        available_width = max(0, available_width)
        self.best_time_container.setFixedSize(available_width, container_height)
        # Finally update the font size
        self._update_font_size(self.best_time_label)


        # Layout might have adjusted sizes slightly, so throughout this function
        # we use the measured values rather than the calculated ones

        # --- Instruction Box ---
        self.instruction_box.setFixedSize(
            int(window_width * INSTRUCTION_BOX_WIDTH),
            int(window_height * INSTRUCTION_BOX_HEIGHT)
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

        self.top_bar.setStyleSheet(f'''
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 {Colors.TOP_BAR.name()}, stop:1 {PySide6.QtGui.QColor.darker(Colors.TOP_BAR, 120).name()});
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        ''')

        # This function overrides the existing method, so we add a call to the
        # parent implementation at the end
        super().resizeEvent(event)
        
    def keyPressEvent(self, event):
        """Handle keyboard events"""
        # Ignore auto-repeat events from holding the key down
        if event.key() == PySide6.QtCore.Qt.Key.Key_Space and not event.isAutoRepeat():
            self.space_indicator.setProperty("pressed", True)
            # Force style update
            self.space_indicator.style().unpolish(self.space_indicator)
            self.space_indicator.style().polish(self.space_indicator)

            self.handle_space_press()
            
    def keyReleaseEvent(self, event):
        """Handle keyboard release events"""
        if event.key() == PySide6.QtCore.Qt.Key.Key_Space:
            self.space_indicator.setProperty("pressed", False)
            self.space_indicator.style().unpolish(self.space_indicator)
            self.space_indicator.style().polish(self.space_indicator)
            
    def handle_space_press(self):
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
            
    def start_waiting(self):
        """Start the waiting period"""
        self.game_state = GameState.WAITING
        self.wait_start_time = time.time()
        self.random_wait_time = random.uniform(2.0, 5.0)
        self.instruction_box.setText('Wait for it...')
        self.timer.start(10)  # Check every 10ms
        
    def too_early(self):
        """Handle early button press"""
        self.game_state = GameState.TOO_EARLY
        self.timer.stop()
        self.instruction_box.setText('Too eager! Try again.\nPress SPACE to continue')
        
        # Shake animation to provide visual feedback for error
        animation = PySide6.QtCore.QPropertyAnimation(self.instruction_box, b"pos")
        animation.setDuration(200)
        start_pos = self.instruction_box.pos()
        
        # Create keyframes for shake effect
        animation.setKeyValueAt(0, start_pos)
        animation.setKeyValueAt(0.2, start_pos + PySide6.QtCore.QPoint(5, 0))
        animation.setKeyValueAt(0.4, start_pos + PySide6.QtCore.QPoint(-5, 0))
        animation.setKeyValueAt(0.6, start_pos + PySide6.QtCore.QPoint(3, 0))
        animation.setKeyValueAt(0.8, start_pos + PySide6.QtCore.QPoint(-3, 0))
        animation.setKeyValueAt(1, start_pos)
        
        animation.start()
        
    def show_result(self):
        """Show reaction time result"""
        self.reaction_time = time.time() - self.start_time
        if self.reaction_time < self.best_time:
            self.best_time = self.reaction_time
            self.best_time_label.setText(f'BEST: {self.best_time:.3f} s')
            if not self.top_bar.isVisible():
                # Recalculate 2nd stretch factor since top bar is now taking up space
                # TODO: Account for 'spacing' between stretches
                layout = self.centralWidget().layout()
                new_stretch = layout.stretch(1) - int(TOP_BAR_HEIGHT * STRETCH_PRECISION)
                layout.setStretch(1, new_stretch)
                self.top_bar.show()

                # --- Animating the trophy ---
                # (It's the little things that make a difference)
                trophy_size = int(self.top_bar.height() * TROPHY_HEIGHT)
                # Use maximumSize instead of size to give the layout manager time to adjust
                # Simply setting size didn't work for me.
                # Additionally, we need to use a b-string in propertyName since Qt's core is written in C++
                self.trophy_animation = PySide6.QtCore.QPropertyAnimation(self.trophy, b"maximumSize")
                self.trophy_animation.setDuration(1000) # ms
                self.trophy_animation.setStartValue(PySide6.QtCore.QSize(0, 0))
                self.trophy_animation.setEndValue(PySide6.QtCore.QSize(trophy_size, trophy_size))
                self.trophy_animation.setEasingCurve(PySide6.QtCore.QEasingCurve.Type.OutBack)
                self.trophy_animation.start()
            # Trigger resize event due to textual content change
            self.resizeEvent(None) 
            
        # Format result text based on performance, to make the game more fun
        if self.reaction_time < 0.05:
            result_text = f'WOW! {self.reaction_time:.3f} seconds\nThat\'s superhuman! Press SPACE to try again'
        elif self.reaction_time < 0.15:
            result_text = f'AMAZING! {self.reaction_time:.3f} seconds\nIncredibly fast! Press SPACE to try again'
        elif self.reaction_time < 0.2:
            result_text = f'EXCELLENT! {self.reaction_time:.3f} seconds\nVery quick reflexes! Press SPACE to try again'
        elif self.reaction_time < 0.4:
            result_text = f'GOOD! {self.reaction_time:.3f} seconds\nSolid performance! Press SPACE to try again'
        else:
            result_text = f'Your time: {self.reaction_time:.3f} seconds\nPress SPACE to try again'
            
        self.game_state = GameState.RESULT
        self.instruction_box.setText(result_text)
        
    def check_wait_time(self):
        """Check if waiting period is over"""
        if time.time() - self.wait_start_time >= self.random_wait_time:
            self.timer.stop()
            self.game_state = GameState.REACT
            self.start_time = time.time()
            self.instruction_box.setText('GO!!!')
            self.instruction_box.setProperty("game_state", "react")
            self._update_font_size(self.instruction_box)
            # Changes don't take effect unless we unpolish and repolish
            self.instruction_box.style().unpolish(self.instruction_box)
            self.instruction_box.style().polish(self.instruction_box)

def main():
    app = PySide6.QtWidgets.QApplication(sys.argv)
    game = ReactionGame()
    game.show()
    sys.exit(app.exec())

# Allows my code to be imported as a module without inherently running the game
if __name__ == '__main__': 
    main()