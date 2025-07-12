
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QCheckBox, QRadioButton, QLineEdit, QPushButton,
    QTextEdit, QFileDialog, QButtonGroup
)
from PySide6.QtCore import QThread, QObject, Signal, Qt

class SearchWorker(QObject):
    """
    Worker thread for performing file search to keep the GUI responsive.
    """
    result_found = Signal(str)
    search_finished = Signal(str)

    def __init__(self, search_path, file_types, phrases, search_mode):
        super().__init__()
        self.search_path = search_path
        self.file_types = file_types
        self.phrases = phrases
        self.search_mode = search_mode
        self.is_cancelled = False

    def run_search(self):
        """

        """
        try:
            include_phrases = [p[1] for p in self.phrases if p[0] == 'include' and p[1]]
            exclude_phrases = [p[1] for p in self.phrases if p[0] == 'exclude' and p[1]]
            files_to_search = self._get_files_to_search()
            count = 0

            for file_path in files_to_search:
                if self.is_cancelled:
                    break
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        if self.search_mode == 'line':
                            for i, line in enumerate(f):
                                if self._check_match(line, include_phrases, exclude_phrases):
                                    self.result_found.emit(f"{file_path}:{i+1}: {line.strip()}")
                                    count += 1
                        else: # 'all' mode
                            content = f.read()
                            if self._check_match(content, include_phrases, exclude_phrases):
                                self.result_found.emit(f"MATCH: {file_path}")
                                count += 1
                except Exception as e:
                    self.result_found.emit(f"ERROR: Cannot read {file_path}: {e}")

            self.search_finished.emit(f"Search complete. Found {count} matches.")
        except Exception as e:
            self.search_finished.emit(f"An error occurred: {e}")


    def _get_files_to_search(self):
        """
        Gathers a list of all files to be searched based on path and extensions.
        """
        files = []
        if os.path.isfile(self.search_path):
            if self._is_valid_extension(self.search_path):
                files.append(self.search_path)
            return files

        for root, _, filenames in os.walk(self.search_path):
            for filename in filenames:
                if self._is_valid_extension(filename):
                    files.append(os.path.join(root, filename))
        return files

    def _is_valid_extension(self, filename):
        """
        Checks if a file's extension matches the selected types.
        """
        if ".*" in self.file_types:
            return True
        return any(filename.endswith(ext) for ext in self.file_types)

    def _check_match(self, content, include, exclude):
        """
        Checks if the content matches the include/exclude criteria.
        """
        has_all_includes = all(p in content for p in include)
        has_any_excludes = any(p in content for p in exclude)
        return has_all_includes and not has_any_excludes

    def cancel(self):
        self.is_cancelled = True


class AdvancedFileSearcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced File Searcher")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self._create_file_types_box()
        self._create_phrases_box()
        self._create_scope_box()
        self._create_controls_box()
        self._create_results_box()

        self.search_thread = None
        self.search_worker = None

    def _create_file_types_box(self):
        group_box = QGroupBox("File Types to Include")
        layout = QHBoxLayout()

        self.cb_md = QCheckBox(".md")
        self.cb_md.setChecked(True)
        self.cb_txt = QCheckBox(".txt")
        self.cb_txt.setChecked(True)
        self.cb_html = QCheckBox(".html")
        self.cb_py = QCheckBox(".py")
        self.cb_custom = QCheckBox("Custom:")
        self.le_custom_ext = QLineEdit()
        self.le_custom_ext.setPlaceholderText("e.g., .css or .*")

        layout.addWidget(self.cb_md)
        layout.addWidget(self.cb_txt)
        layout.addWidget(self.cb_html)
        layout.addWidget(self.cb_py)
        layout.addWidget(self.cb_custom)
        layout.addWidget(self.le_custom_ext)
        layout.addStretch()

        group_box.setLayout(layout)
        self.layout.addWidget(group_box)

    def _create_phrases_box(self):
        group_box = QGroupBox("Search Phrases")
        layout = QVBoxLayout()
        self.phrase_widgets = []

        for i in range(5):
            h_layout = QHBoxLayout()
            bg = QButtonGroup(self)

            rb_include = QRadioButton("Include (+)")
            rb_include.setChecked(True)
            rb_exclude = QRadioButton("Exclude (-)")
            le_phrase = QLineEdit()
            le_phrase.setPlaceholderText(f"Phrase {i+1}")

            bg.addButton(rb_include)
            bg.addButton(rb_exclude)

            h_layout.addWidget(rb_include)
            h_layout.addWidget(rb_exclude)
            h_layout.addWidget(le_phrase)
            layout.addLayout(h_layout)
            self.phrase_widgets.append((rb_include, le_phrase))

        group_box.setLayout(layout)
        self.layout.addWidget(group_box)

    def _create_scope_box(self):
        group_box = QGroupBox("Search Scope & Options")
        layout = QVBoxLayout()
        
        # Path selection
        path_layout = QHBoxLayout()
        self.le_path = QLineEdit()
        self.le_path.setReadOnly(True)
        self.le_path.setPlaceholderText("Select a starting file or directory...")
        btn_browse_dir = QPushButton("Select Directory...")
        btn_browse_dir.clicked.connect(self.browse_directory)
        btn_browse_file = QPushButton("Select File...")
        btn_browse_file.clicked.connect(self.browse_file)

        path_layout.addWidget(self.le_path)
        path_layout.addWidget(btn_browse_dir)
        path_layout.addWidget(btn_browse_file)
        layout.addLayout(path_layout)

        # Search mode (Line vs All)
        mode_layout = QHBoxLayout()
        self.search_mode_group = QButtonGroup(self)
        self.rb_line = QRadioButton("Search by Line")
        self.rb_line.setChecked(True)
        self.rb_all = QRadioButton("Search Entire File")
        self.search_mode_group.addButton(self.rb_line)
        self.search_mode_group.addButton(self.rb_all)
        mode_layout.addWidget(self.rb_line)
        mode_layout.addWidget(self.rb_all)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        group_box.setLayout(layout)
        self.layout.addWidget(group_box)

    def _create_controls_box(self):
        self.btn_search = QPushButton("Start Search")
        self.btn_search.clicked.connect(self.start_search)
        self.layout.addWidget(self.btn_search)

    def _create_results_box(self):
        group_box = QGroupBox("Results")
        layout = QVBoxLayout()
        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)
        layout.addWidget(self.results_area)
        group_box.setLayout(layout)
        self.layout.addWidget(group_box)

    def browse_directory(self):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            self.le_path.setText(path)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if path:
            self.le_path.setText(path)

    def start_search(self):
        search_path = self.le_path.text()
        if not search_path:
            self.results_area.setText("Please select a search path first.")
            return

        # Stop previous search if running
        if self.search_thread and self.search_thread.isRunning():
            self.search_worker.cancel()
            self.search_thread.quit()
            self.search_thread.wait()

        self.results_area.clear()
        self.btn_search.setText("Searching...")
        self.btn_search.setEnabled(False)

        file_types = []
        if self.cb_md.isChecked(): file_types.append(".md")
        if self.cb_txt.isChecked(): file_types.append(".txt")
        if self.cb_html.isChecked(): file_types.append(".html")
        if self.cb_py.isChecked(): file_types.append(".py")
        if self.cb_custom.isChecked() and self.le_custom_ext.text():
            file_types.append(self.le_custom_ext.text())

        phrases = []
        for rb_include, le_phrase in self.phrase_widgets:
            mode = 'include' if rb_include.isChecked() else 'exclude'
            phrases.append((mode, le_phrase.text()))

        search_mode = 'line' if self.rb_line.isChecked() else 'all'

        self.search_thread = QThread()
        self.search_worker = SearchWorker(search_path, file_types, phrases, search_mode)
        self.search_worker.moveToThread(self.search_thread)

        self.search_thread.started.connect(self.search_worker.run_search)
        self.search_worker.result_found.connect(self.append_result)
        self.search_worker.search_finished.connect(self.on_search_finished)
        
        self.search_thread.start()

    def append_result(self, result_text):
        self.results_area.append(result_text)

    def on_search_finished(self, message):
        self.results_area.append(message)
        self.btn_search.setText("Start Search")
        self.btn_search.setEnabled(True)
        self.search_thread.quit()
        self.search_thread.wait()


    def closeEvent(self, event):
        # Clean up the thread when closing the application
        if self.search_thread and self.search_thread.isRunning():
            self.search_worker.cancel()
            self.search_thread.quit()
            self.search_thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvancedFileSearcher()
    window.show()
    sys.exit(app.exec())
