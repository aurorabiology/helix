import sys
import traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QDockWidget, QFileDialog,
    QMessageBox, QProgressBar, QAction, QToolBar, QLabel, QStatusBar, QWidget, QVBoxLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon

# Import your HelixLang internal modules here
from helixlang.gui.editor import CodeEditor
from helixlang.gui.visualizer import Visualizer3D
from helixlang.gui.settings import SettingsManager
from helixlang.simulation import run_simulation_async  # Hypothetical async sim API
from helixlang.compiler import compile_and_run_code  # Core compile & run API


class SimulationThread(QThread):
    """
    Run long simulations asynchronously to avoid UI blocking.
    Emits progress updates and completion signals.
    """
    progress_changed = pyqtSignal(int)
    simulation_finished = pyqtSignal(object)  # Results or Exception

    def __init__(self, protein_data, duration):
        super().__init__()
        self.protein_data = protein_data
        self.duration = duration
        self._cancel_requested = False

    def run(self):
        try:
            # Example simulation loop that periodically reports progress
            for progress in run_simulation_async(self.protein_data, self.duration):
                if self._cancel_requested:
                    self.simulation_finished.emit(None)
                    return
                self.progress_changed.emit(progress)
            results = "Simulation complete with results"  # Replace with actual results
            self.simulation_finished.emit(results)
        except Exception as e:
            self.simulation_finished.emit(e)

    def cancel(self):
        self._cancel_requested = True


class HelixMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HelixLang IDE")
        self.setWindowIcon(QIcon(":/icons/helix_icon.png"))
        self.resize(1200, 800)

        # Load user settings
        self.settings = SettingsManager.load()

        # Setup central editor tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create first editor tab
        self.editor = CodeEditor()
        self.editor.set_syntax_highlighting("helixlang")
        self.tabs.addTab(self.editor, "Untitled.hlx")
        self.current_file = None
        self.is_modified = False

        # Connect editor change signal
        self.editor.codeChanged.connect(self.on_code_modified)

        # Setup dock widgets
        self.setup_visualizer_dock()
        self.setup_output_console_dock()

        # Status bar with progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)

        # Setup actions, menus, toolbars
        self.create_actions()
        self.create_menus()
        self.create_toolbar()

        # Simulation thread placeholder
        self.sim_thread = None

    def setup_visualizer_dock(self):
        self.visualizer_dock = QDockWidget("3D Visualizer", self)
        self.visualizer = Visualizer3D()
        self.visualizer_dock.setWidget(self.visualizer)
        self.visualizer_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.visualizer_dock)

    def setup_output_console_dock(self):
        self.output_dock = QDockWidget("Output Console", self)
        self.output_console = QLabel()
        self.output_console.setWordWrap(True)
        self.output_console.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        self.output_dock.setWidget(self.output_console)
        self.output_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.output_dock)

    def create_actions(self):
        self.action_new = QAction("New", self)
        self.action_new.setShortcut("Ctrl+N")
        self.action_new.triggered.connect(self.new_file)

        self.action_open = QAction("Open...", self)
        self.action_open.setShortcut("Ctrl+O")
        self.action_open.triggered.connect(self.open_file)

        self.action_save = QAction("Save", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.triggered.connect(self.save_file)

        self.action_save_as = QAction("Save As...", self)
        self.action_save_as.triggered.connect(self.save_file_as)

        self.action_exit = QAction("Exit", self)
        self.action_exit.triggered.connect(self.close)

        self.action_run_sim = QAction("Run Simulation", self)
        self.action_run_sim.setShortcut("F5")
        self.action_run_sim.triggered.connect(self.run_simulation)

        self.action_stop_sim = QAction("Stop Simulation", self)
        self.action_stop_sim.triggered.connect(self.stop_simulation)
        self.action_stop_sim.setEnabled(False)

    def create_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_open)
        file_menu.addAction(self.action_save)
        file_menu.addAction(self.action_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

        run_menu = menubar.addMenu("Run")
        run_menu.addAction(self.action_run_sim)
        run_menu.addAction(self.action_stop_sim)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.addAction(self.action_new)
        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)
        toolbar.addSeparator()
        toolbar.addAction(self.action_run_sim)
        toolbar.addAction(self.action_stop_sim)

    def new_file(self):
        if self.is_modified:
            if not self.confirm_discard_changes():
                return
        new_editor = CodeEditor()
        new_editor.set_syntax_highlighting("helixlang")
        new_editor.codeChanged.connect(self.on_code_modified)
        self.tabs.addTab(new_editor, "Untitled.hlx")
        self.tabs.setCurrentWidget(new_editor)
        self.current_file = None
        self.is_modified = False

    def open_file(self):
        if self.is_modified:
            if not self.confirm_discard_changes():
                return
        path, _ = QFileDialog.getOpenFileName(self, "Open HelixLang File", "", "HelixLang Files (*.hlx);;All Files (*)")
        if path:
            try:
                with open(path, 'r') as f:
                    code = f.read()
                editor = CodeEditor()
                editor.set_syntax_highlighting("helixlang")
                editor.setPlainText(code)
                editor.codeChanged.connect(self.on_code_modified)
                self.tabs.addTab(editor, path)
                self.tabs.setCurrentWidget(editor)
                self.current_file = path
                self.is_modified = False
            except Exception as e:
                QMessageBox.critical(self, "Error Opening File", f"Could not open file:\n{str(e)}")

    def save_file(self):
        if self.current_file:
            self._save_to_path(self.current_file)
        else:
            self.save_file_as()

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save HelixLang File", "", "HelixLang Files (*.hlx);;All Files (*)")
        if path:
            self._save_to_path(path)

    def _save_to_path(self, path):
        try:
            current_editor = self.tabs.currentWidget()
            if not isinstance(current_editor, CodeEditor):
                return
            with open(path, 'w') as f:
                f.write(current_editor.toPlainText())
            self.current_file = path
            self.tabs.setTabText(self.tabs.currentIndex(), path)
            self.is_modified = False
            self.statusBar().showMessage(f"Saved to {path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")

    def confirm_discard_changes(self):
        ret = QMessageBox.warning(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to discard them?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return ret == QMessageBox.Yes

    def on_code_modified(self):
        self.is_modified = True

    def run_simulation(self):
        # Disable run button, enable stop
        self.action_run_sim.setEnabled(False)
        self.action_stop_sim.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.output_console.setText("Starting simulation...\n")

        # Get protein data from current editor content (stub)
        code = self.tabs.currentWidget().toPlainText()
        try:
            protein_data = compile_and_run_code(code)  # Simplified example
        except Exception as e:
            QMessageBox.critical(self, "Compile Error", str(e))
            self.reset_simulation_ui()
            return

        self.sim_thread = SimulationThread(protein_data, duration=100)
        self.sim_thread.progress_changed.connect(self.progress_bar.setValue)
        self.sim_thread.simulation_finished.connect(self.on_simulation_finished)
        self.sim_thread.start()

    @pyqtSlot(object)
    def on_simulation_finished(self, result):
        if isinstance(result, Exception):
            self.output_console.setText(f"Simulation failed:\n{str(result)}\n{traceback.format_exc()}")
        elif result is None:
            self.output_console.setText("Simulation cancelled.")
        else:
            self.output_console.setText(f"Simulation completed successfully:\n{result}")
            self.visualizer.display_simulation_results(result)

        self.reset_simulation_ui()

    def reset_simulation_ui(self):
        self.action_run_sim.setEnabled(True)
        self.action_stop_sim.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.sim_thread = None

    def stop_simulation(self):
        if self.sim_thread:
            self.sim_thread.cancel()

    def closeEvent(self, event):
        if self.is_modified:
            if not self.confirm_discard_changes():
                event.ignore()
                return
        self.settings.save()  # Save user settings on close
        event.accept()


def main():
    app = QApplication(sys.argv)
    main_win = HelixMainWindow()
    main_win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
