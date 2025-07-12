import os
import subprocess
import datetime
import sys
import json
import webbrowser
import difflib
import re
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QListWidget,
    QPushButton, QMessageBox, QHBoxLayout, QTextEdit, QSplitter,
    QFileDialog, QListWidgetItem, QCheckBox, QScrollArea, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor

class GitTimeTravel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("\U0001F570️ Himalaya Git Time Travel Console")
        self.setMinimumWidth(900)

        self.repo_path = os.getcwd()
        self.repo_name = os.path.basename(self.repo_path)
        self.github_user = "CallMeChewy"
        self.config = self.load_himalaya_config()
        self.repo_url = f"https://github.com/{self.github_user}/{self.repo_name}"
        self.current_branch = ""
        self.selected_file = None
        self.file_commits = set()
        self.diff_window = None
        self.commit_files = {}
        self.updating_dropdown = False

        self.init_ui()
        self.populate_commits()

    def init_ui(self):
        layout = QVBoxLayout()

        self.status_label = QLabel("\U0001F50D Verifying Git status...")
        layout.addWidget(self.status_label)

        self.repo_link = QPushButton(f"\U0001F4CE View {self.repo_name} on GitHub")
        self.repo_link.clicked.connect(self.open_repo_url)
        layout.addWidget(self.repo_link)

        # File selection section
        file_layout = QHBoxLayout()
        self.select_file_button = QPushButton("\U0001F4C1 Select File to Track")
        self.select_file_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.select_file_button)
        
        self.selected_file_label = QLabel("No file selected")
        self.selected_file_label.setWordWrap(True)
        file_layout.addWidget(self.selected_file_label)
        
        layout.addLayout(file_layout)

        self.commit_list = QListWidget()
        self.commit_list.currentRowChanged.connect(self.show_diff)
        self.commit_list.currentRowChanged.connect(self.update_py_files_dropdown)

        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)

        # File diff button
        self.file_diff_button = QPushButton("🔍 Compare Selected File with Commit")
        self.file_diff_button.clicked.connect(self.show_file_diff)
        self.file_diff_button.setEnabled(False)
        layout.addWidget(self.file_diff_button)

        # Main content area with commit list and file selector
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - commit list
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        commit_label = QLabel("Commit History:")
        commit_label.setStyleSheet("font-weight: bold; padding: 5px;")
        left_layout.addWidget(commit_label)
        
        left_layout.addWidget(self.commit_list)
        left_widget.setLayout(left_layout)
        main_splitter.addWidget(left_widget)
        
        # Right side - file selector and diff view
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # File selector section
        file_selector_label = QLabel("Web Files Changed in Selected Commit (.py, .js, .css, .html):")
        file_selector_label.setStyleSheet("font-weight: bold; padding: 5px;")
        right_layout.addWidget(file_selector_label)
        
        self.web_files_combo = QComboBox()
        self.web_files_combo.currentTextChanged.connect(self.on_web_file_selected)
        right_layout.addWidget(self.web_files_combo)
        
        # Diff view
        right_layout.addWidget(self.diff_view)
        
        right_widget.setLayout(right_layout)
        main_splitter.addWidget(right_widget)
        
        # Set initial splitter sizes (commit list takes 60%, file selector takes 40%)
        main_splitter.setSizes([600, 400])
        
        layout.addWidget(main_splitter)

        button_layout = QHBoxLayout()
        self.travel_button = QPushButton("\U0001F6F1 Travel to Selected Commit")
        self.travel_button.clicked.connect(self.travel_to_commit)
        button_layout.addWidget(self.travel_button)

        self.undo_button = QPushButton("\u21a9 Return to Original Branch")
        self.undo_button.clicked.connect(self.return_to_origin)
        self.undo_button.setEnabled(False)
        button_layout.addWidget(self.undo_button)

        self.exit_button = QPushButton("\u274C Exit")
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.exit_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_himalaya_config(self):
        config_path = os.path.join(self.repo_path, ".himalaya.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def open_repo_url(self):
        webbrowser.open(self.repo_url)

    def populate_commits(self):
        try:
            self.current_branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                text=True
            ).strip()
            self.status_label.setText(f"\U0001F4CD Current Branch: {self.current_branch}")

            raw_logs = subprocess.check_output([
                "git", "log", "--pretty=format:%H|%h %ad %s",
                "--date=short", "-n", "30"
            ], text=True).splitlines()

            self.commits = []
            self.commit_list.clear()
            for line in raw_logs:
                full_hash, desc = line.split("|", 1)
                self.commits.append((full_hash.strip(), desc.strip()))
                self.commit_list.addItem(desc.strip())
            
            # Update file highlighting if a file is selected
            if self.selected_file:
                self.get_file_commits()
                self.update_commit_highlighting()
            
            # Load commit files for dropdowns
            self.load_commit_files()
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Git Error", "\u274C Not a Git repository or Git not found.")
            self.close()

    def show_diff(self, index):
        if index < 0 or index >= len(self.commits):
            self.diff_view.setText("")
            return
        commit_hash, _ = self.commits[index]
        
        # If a specific file is selected, show diff for that file only
        if self.selected_file:
            try:
                diff_text = subprocess.check_output(
                    ["git", "diff", f"{commit_hash}..{self.current_branch}", "--", self.selected_file],
                    text=True, stderr=subprocess.DEVNULL
                )
                if diff_text:
                    self.diff_view.setText(f"Diff for {self.selected_file}:\n\n{diff_text}")
                else:
                    self.diff_view.setText(f"✅ No differences in {self.selected_file} from current branch.")
            except subprocess.CalledProcessError:
                self.diff_view.setText(f"⚠️ Could not generate diff for {self.selected_file}.")
        else:
            # Show full commit diff
            try:
                diff_text = subprocess.check_output(
                    ["git", "diff", f"{commit_hash}..{self.current_branch}"],
                    text=True, stderr=subprocess.DEVNULL
                )
                self.diff_view.setText(diff_text if diff_text else "✅ No differences from current branch.")
            except subprocess.CalledProcessError:
                self.diff_view.setText("⚠️ Could not generate diff.")

    def stash_wip(self):
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if result.stdout.strip():
            subprocess.run(["git", "stash", "push", "-m", "Time travel WIP stash"])
            return True
        return False

    def travel_to_commit(self):
        def run_restore_mtime():
            try:
                subprocess.run(["git", "restore-mtime"], check=True, stdout=subprocess.DEVNULL)
                print("✅ File timestamps restored based on commit history.")
            except FileNotFoundError:
                print("⚠️ git-restore-mtime not found. Run 'pip install git-restore-mtime' if audit accuracy is required.")
            except subprocess.CalledProcessError:
                print("❌ Failed to run git-restore-mtime.")

        index = self.commit_list.currentRow()
        if index < 0:
            QMessageBox.warning(self, "No Selection", "⚠️ Please select a commit from the list.")
            return

        commit_hash, desc = self.commits[index]

        answer = QMessageBox.question(
            self,
            "Checkout Confirmation",
            f"🧭 Travel to:\n\n{desc}\n\nCreate a temporary branch?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )

        if answer == QMessageBox.StandardButton.Cancel:
            return

        try:
            self.origin_branch = self.current_branch
            self.stashed = self.stash_wip()

            if answer == QMessageBox.StandardButton.Yes:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                branch_name = f"travel_{timestamp}"
                subprocess.check_call(["git", "switch", "-c", branch_name, commit_hash])
                msg = f"✅ Switched to new branch:\n  {branch_name}"
            else:
                subprocess.check_call(["git", "switch", "--detach", commit_hash])
                msg = f"✅ Detached HEAD at:\n  {desc}"

            QMessageBox.information(
                self,
                "Time Travel Success",
                f"""{msg}

To return: click Return to Original Branch button.

📎 Online:
  {self.repo_url}/commit/{commit_hash}"""
            )

            self.undo_button.setEnabled(True)
            run_restore_mtime()

        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Git Checkout Failed", f"❌ Error while switching:\n{e}")

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Track",
            self.repo_path,
            "All Files (*)"
        )
        if file_path:
            # Make path relative to repo root
            try:
                self.selected_file = os.path.relpath(file_path, self.repo_path)
                self.selected_file_label.setText(f"📄 Tracking: {self.selected_file}")
                self.get_file_commits()
                self.update_commit_highlighting()
                self.file_diff_button.setEnabled(True)
            except ValueError:
                QMessageBox.warning(self, "Invalid File", "Please select a file within the repository.")
    
    def get_file_commits(self):
        if not self.selected_file:
            return
        
        try:
            # Get commits that modified the selected file
            result = subprocess.check_output([
                "git", "log", "--pretty=format:%H", "--", self.selected_file
            ], text=True)
            
            self.file_commits = set(result.strip().split('\n')) if result.strip() else set()
        except subprocess.CalledProcessError:
            self.file_commits = set()
    
    def update_commit_highlighting(self):
        for i in range(self.commit_list.count()):
            item = self.commit_list.item(i)
            commit_hash = self.commits[i][0]
            
            if commit_hash in self.file_commits:
                # Highlight commits that contain changes to the selected file
                font = QFont()
                font.setBold(True)
                item.setFont(font)
                # Add indicator to the text
                original_text = item.text()
                if not original_text.startswith("📝 "):
                    item.setText(f"📝 {original_text}")
            else:
                # Remove highlighting
                font = QFont()
                font.setBold(False)
                item.setFont(font)
                # Remove indicator from text
                original_text = item.text()
                if original_text.startswith("📝 "):
                    item.setText(original_text[3:])
    
    def load_commit_files(self):
        """Load web development files (.py, .js, .css, .html) changed in each commit"""
        self.commit_files = {}
        
        for commit_hash, _ in self.commits:
            try:
                # Get files changed in this commit
                result = subprocess.check_output([
                    "git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash
                ], text=True, cwd=self.repo_path)
                
                # Filter for web development files
                web_files = []
                for f in result.strip().split('\n'):
                    if f.strip() and any(f.endswith(ext) for ext in ['.py', '.js', '.css', '.html']):
                        web_files.append(f)
                
                self.commit_files[commit_hash] = web_files
                
            except subprocess.CalledProcessError:
                self.commit_files[commit_hash] = []
    
    def update_py_files_dropdown(self, index):
        """Update the dropdown with web files from the selected commit"""
        self.updating_dropdown = True  # Prevent auto-launch during update
        self.web_files_combo.clear()
        
        if index < 0 or index >= len(self.commits):
            self.updating_dropdown = False
            return
            
        commit_hash = self.commits[index][0]
        web_files = self.commit_files.get(commit_hash, [])
        
        if web_files:
            self.web_files_combo.addItems(web_files)
            # If the currently selected file is in the list, select it
            if self.selected_file and self.selected_file in web_files:
                self.web_files_combo.setCurrentText(self.selected_file)
        else:
            self.web_files_combo.addItem("No web files (.py, .js, .css, .html) changed in this commit")
        
        self.updating_dropdown = False  # Re-enable auto-launch
    
    def on_web_file_selected(self, file_path):
        """Handle selection of a web file from the dropdown"""
        if file_path and file_path != "No web files (.py, .js, .css, .html) changed in this commit":
            self.selected_file = file_path
            self.selected_file_label.setText(f"📄 Tracking: {self.selected_file}")
            self.file_diff_button.setEnabled(True)
            self.get_file_commits()
            self.update_commit_highlighting()
            # Update the diff view to show this file
            self.show_diff(self.commit_list.currentRow())
            
            # Only auto-launch diff window if user manually selected from dropdown
            # (not when dropdown is being populated programmatically)
            if not self.updating_dropdown:
                self.show_file_diff()

    def show_file_diff(self):
        if not self.selected_file:
            QMessageBox.warning(self, "No File Selected", "Please select a file to compare first.")
            return
        
        index = self.commit_list.currentRow()
        if index < 0:
            QMessageBox.warning(self, "No Commit Selected", "Please select a commit to compare with.")
            return
        
        commit_hash = self.commits[index][0]
        
        # Create and show diff window
        self.diff_window = FileDiffWindow(self.repo_path, self.selected_file, commit_hash)
        self.diff_window.show()

    def return_to_origin(self):
        try:
            subprocess.check_call(["git", "switch", self.origin_branch])
            if self.stashed:
                subprocess.run(["git", "stash", "pop"])
            QMessageBox.information(self, "Returned", f"✅ Back on {self.origin_branch}.")
            self.undo_button.setEnabled(False)
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Restore Failed", f"❌ Could not return: {e}")

class FileDiffWindow(QWidget):
    def __init__(self, repo_path, file_path, commit_hash):
        super().__init__()
        self.repo_path = repo_path
        self.file_path = file_path
        self.commit_hash = commit_hash
        self.show_full_file = True
        self.is_fullscreen = False
        self.normal_geometry = None
        
        self.setWindowTitle(f"File Comparison: {file_path}")
        self.setMinimumSize(1200, 800)
        
        self.init_ui()
        self.load_file_contents()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Minimal header with close button
        header_layout = QHBoxLayout()
        
        file_info = QLabel(f"📝 {self.file_path}")
        file_info.setStyleSheet("font-size: 13px; font-weight: bold; color: #555;")
        header_layout.addWidget(file_info)
        
        header_layout.addStretch()
        
        # Toggle view button
        self.toggle_button = QPushButton("Diff Only")
        self.toggle_button.clicked.connect(self.toggle_diff_view)
        self.toggle_button.setStyleSheet("font-size: 11px; padding: 3px 8px; background-color: #f0f0f0; border: 1px solid #ccc;")
        header_layout.addWidget(self.toggle_button)
        
        # Fullscreen toggle button
        self.fullscreen_button = QPushButton("⛶")
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.fullscreen_button.setStyleSheet("font-size: 12px; padding: 3px 8px; background-color: #e3f2fd; border: 1px solid #2196f3; color: #1976d2;")
        self.fullscreen_button.setToolTip("Toggle Fullscreen (F11)")
        header_layout.addWidget(self.fullscreen_button)
        
        close_button = QPushButton("×")
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px 6px; background-color: #f44336; color: white; border: none;")
        header_layout.addWidget(close_button)
        
        layout.addLayout(header_layout)
        
        # Diff display
        self.diff_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Local file (original)
        left_layout = QVBoxLayout()
        left_label = QLabel("🟢 Local File (Current)")
        left_label.setStyleSheet("font-weight: bold; background-color: #e8f8e8; color: #2e7d32; padding: 8px; font-size: 12px;")
        left_layout.addWidget(left_label)
        
        self.local_text = QTextEdit()
        self.local_text.setReadOnly(True)
        self.local_text.setFont(QFont("Consolas", 11))
        self.local_text.setStyleSheet("background-color: #fafafa; color: #333; border: 1px solid #ddd; selection-background-color: #e3f2fd;")
        self.local_text.verticalScrollBar().valueChanged.connect(self.sync_scroll_right)
        left_layout.addWidget(self.local_text)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        self.diff_splitter.addWidget(left_widget)
        
        # Right side - Commit file (historical)
        right_layout = QVBoxLayout()
        right_label = QLabel(f"🔴 Commit {self.commit_hash[:8]} (Historical)")
        right_label.setStyleSheet("font-weight: bold; background-color: #ffeaea; color: #c62828; padding: 8px; font-size: 12px;")
        right_layout.addWidget(right_label)
        
        self.commit_text = QTextEdit()
        self.commit_text.setReadOnly(True)
        self.commit_text.setFont(QFont("Consolas", 11))
        self.commit_text.setStyleSheet("background-color: #fafafa; color: #333; border: 1px solid #ddd; selection-background-color: #ffebee;")
        self.commit_text.verticalScrollBar().valueChanged.connect(self.sync_scroll_left)
        right_layout.addWidget(self.commit_text)
        
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        self.diff_splitter.addWidget(right_widget)
        
        layout.addWidget(self.diff_splitter)
        self.setLayout(layout)
        
    def load_file_contents(self):
        try:
            # Get local file content
            local_file_path = os.path.join(self.repo_path, self.file_path)
            if os.path.exists(local_file_path):
                with open(local_file_path, 'r', encoding='utf-8') as f:
                    self.local_content = f.read()
            else:
                self.local_content = "File not found in current working directory"
            
            # Get commit file content
            try:
                self.commit_content = subprocess.check_output([
                    "git", "show", f"{self.commit_hash}:{self.file_path}"
                ], text=True, cwd=self.repo_path)
            except subprocess.CalledProcessError:
                self.commit_content = "File not found in this commit"
            
            # Update window title
            self.setWindowTitle(f"File Comparison: {self.file_path}")
            
            self.update_display()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file contents: {e}")
    
    def update_display(self):
        if self.show_full_file:
            self.show_full_files()
        else:
            self.show_diff_only()
    
    def show_full_files(self):
        # Display full files with highlighting
        local_lines = self.local_content.splitlines()
        commit_lines = self.commit_content.splitlines()
        
        # Create unified diff to identify changes
        diff = list(difflib.unified_diff(commit_lines, local_lines, lineterm=''))
        
        # Parse diff to identify changed lines
        local_changes = set()
        commit_changes = set()
        
        local_line_num = 0
        commit_line_num = 0
        
        for line in diff:
            if line.startswith('@@'):
                # Parse line numbers from diff header
                match = re.search(r'-(?P<commit_start>\d+)(?:,(?P<commit_count>\d+))? \+(?P<local_start>\d+)(?:,(?P<local_count>\d+))?', line)
                if match:
                    commit_line_num = int(match.group('commit_start')) - 1
                    local_line_num = int(match.group('local_start')) - 1
            elif line.startswith('-'):
                commit_changes.add(commit_line_num)
                commit_line_num += 1
            elif line.startswith('+'):
                local_changes.add(local_line_num)
                local_line_num += 1
            elif line.startswith(' '):
                commit_line_num += 1
                local_line_num += 1
        
        # Display local file with highlighting
        self.local_text.clear()
        for i, line in enumerate(local_lines):
            if i in local_changes:
                self.local_text.setTextColor(QColor(27, 94, 32))  # Dark green for changes
                self.local_text.append(f"{i+1:4d}: {line}")
            else:
                self.local_text.setTextColor(QColor(55, 71, 79))  # Dark gray for unchanged
                self.local_text.append(f"{i+1:4d}: {line}")
        
        # Display commit file with highlighting
        self.commit_text.clear()
        for i, line in enumerate(commit_lines):
            if i in commit_changes:
                self.commit_text.setTextColor(QColor(183, 28, 28))  # Dark red for changes
                self.commit_text.append(f"{i+1:4d}: {line}")
            else:
                self.commit_text.setTextColor(QColor(55, 71, 79))  # Dark gray for unchanged
                self.commit_text.append(f"{i+1:4d}: {line}")
    
    def show_diff_only(self):
        # Show only the differences in side-by-side format
        local_lines = self.local_content.splitlines()
        commit_lines = self.commit_content.splitlines()
        
        differ = difflib.SequenceMatcher(None, commit_lines, local_lines)
        
        # Build diff-only display lists
        local_diff_display = []
        commit_diff_display = []
        
        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag != 'equal':  # Only show changes, not equal lines
                if tag == 'replace':
                    # Lines are different
                    commit_chunk = commit_lines[i1:i2]
                    local_chunk = local_lines[j1:j2]
                    max_len = max(len(commit_chunk), len(local_chunk))
                    
                    for i in range(max_len):
                        if i < len(commit_chunk):
                            commit_diff_display.append((i1 + i + 1, commit_chunk[i], 'changed'))
                        else:
                            commit_diff_display.append(('', '', 'empty'))
                        
                        if i < len(local_chunk):
                            local_diff_display.append((j1 + i + 1, local_chunk[i], 'changed'))
                        else:
                            local_diff_display.append(('', '', 'empty'))
                
                elif tag == 'delete':
                    # Lines deleted from commit
                    for i, line in enumerate(commit_lines[i1:i2]):
                        commit_diff_display.append((i1 + i + 1, line, 'deleted'))
                        local_diff_display.append(('', '(deleted)', 'empty'))
                
                elif tag == 'insert':
                    # Lines added to local
                    for i, line in enumerate(local_lines[j1:j2]):
                        local_diff_display.append((j1 + i + 1, line, 'added'))
                        commit_diff_display.append(('', '(added)', 'empty'))
        
        # Display commit differences
        self.commit_text.clear()
        if commit_diff_display:
            for line_num, line_content, line_type in commit_diff_display:
                if line_type == 'changed' or line_type == 'deleted':
                    self.commit_text.setTextColor(QColor(183, 28, 28))  # Dark red
                else:
                    self.commit_text.setTextColor(QColor(150, 150, 150))  # Light gray for empty
                
                if line_num:
                    self.commit_text.append(f"{line_num:4d}: {line_content}")
                else:
                    self.commit_text.append(f"     {line_content}")
        else:
            self.commit_text.setTextColor(QColor(55, 71, 79))
            self.commit_text.append("No changes in commit version")
        
        # Display local differences
        self.local_text.clear()
        if local_diff_display:
            for line_num, line_content, line_type in local_diff_display:
                if line_type == 'changed' or line_type == 'added':
                    self.local_text.setTextColor(QColor(27, 94, 32))  # Dark green
                else:
                    self.local_text.setTextColor(QColor(150, 150, 150))  # Light gray for empty
                
                if line_num:
                    self.local_text.append(f"{line_num:4d}: {line_content}")
                else:
                    self.local_text.append(f"     {line_content}")
        else:
            self.local_text.setTextColor(QColor(55, 71, 79))
            self.local_text.append("No changes in local version")
    
    def sync_scroll_left(self, value):
        """Sync scrolling from commit text to local text"""
        if hasattr(self, '_syncing_scroll') and self._syncing_scroll:
            return
        self._syncing_scroll = True
        self.local_text.verticalScrollBar().setValue(value)
        self._syncing_scroll = False
    
    def sync_scroll_right(self, value):
        """Sync scrolling from local text to commit text"""
        if hasattr(self, '_syncing_scroll') and self._syncing_scroll:
            return
        self._syncing_scroll = True
        self.commit_text.verticalScrollBar().setValue(value)
        self._syncing_scroll = False
    
    def toggle_diff_view(self):
        self.show_full_file = not self.show_full_file
        self.toggle_button.setText("Full Files" if not self.show_full_file else "Diff Only")
        self.update_display()
    
    def open_fullscreen_diff(self):
        # Create a new fullscreen window with only the diff areas
        fullscreen_window = FullscreenDiffWindow(
            self.local_content, 
            self.commit_content, 
            self.file_path, 
            self.commit_hash,
            self.show_full_file
        )
        fullscreen_window.showFullScreen()
    
    def toggle_fullscreen(self):
        if self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
        else:
            self.showFullScreen()
            self.is_fullscreen = True

class FullscreenDiffWindow(QWidget):
    def __init__(self, local_content, commit_content, file_path, commit_hash, show_full_file):
        super().__init__()
        self.local_content = local_content
        self.commit_content = commit_content
        self.file_path = file_path
        self.commit_hash = commit_hash
        self.show_full_file = show_full_file
        
        self.setWindowTitle(f"Fullscreen Diff: {file_path}")
        self.setStyleSheet("background-color: #1e1e1e; color: white;")
        
        self.init_ui()
        self.update_display()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Top control bar
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(10, 5, 10, 5)
        
        # File info
        file_info = QLabel(f"📄 {self.file_path} | Commit: {self.commit_hash[:8]}")
        file_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        control_layout.addWidget(file_info)
        
        control_layout.addStretch()
        
        # Toggle view button
        self.toggle_view_button = QPushButton("Show Diff Only" if self.show_full_file else "Show Full Files")
        self.toggle_view_button.clicked.connect(self.toggle_view)
        self.toggle_view_button.setStyleSheet("background-color: #333; color: white; padding: 5px 10px; border: 1px solid #555;")
        control_layout.addWidget(self.toggle_view_button)
        
        # Close button
        close_button = QPushButton("❌ Close")
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("background-color: #d32f2f; color: white; padding: 5px 10px; border: none;")
        control_layout.addWidget(close_button)
        
        layout.addLayout(control_layout)
        
        # Main diff area
        self.diff_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.diff_splitter.setStyleSheet("QSplitter::handle { background-color: #555; }")
        
        # Left panel - Local file
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_header = QLabel("🟢 Local File (Original)")
        left_header.setStyleSheet("font-weight: bold; background-color: #2e7d32; color: white; padding: 8px; font-size: 12px;")
        left_layout.addWidget(left_header)
        
        self.local_text = QTextEdit()
        self.local_text.setReadOnly(True)
        self.local_text.setFont(QFont("Consolas", 11))
        self.local_text.setStyleSheet("background-color: #252525; color: #ffffff; border: none; selection-background-color: #404040;")
        self.local_text.verticalScrollBar().valueChanged.connect(self.sync_scroll_right_fullscreen)
        left_layout.addWidget(self.local_text)
        
        left_widget.setLayout(left_layout)
        self.diff_splitter.addWidget(left_widget)
        
        # Right panel - Commit file
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_header = QLabel("🔴 Commit File (New)")
        right_header.setStyleSheet("font-weight: bold; background-color: #c62828; color: white; padding: 8px; font-size: 12px;")
        right_layout.addWidget(right_header)
        
        self.commit_text = QTextEdit()
        self.commit_text.setReadOnly(True)
        self.commit_text.setFont(QFont("Consolas", 11))
        self.commit_text.setStyleSheet("background-color: #252525; color: #ffffff; border: none; selection-background-color: #404040;")
        self.commit_text.verticalScrollBar().valueChanged.connect(self.sync_scroll_left_fullscreen)
        right_layout.addWidget(self.commit_text)
        
        right_widget.setLayout(right_layout)
        self.diff_splitter.addWidget(right_widget)
        
        layout.addWidget(self.diff_splitter)
        self.setLayout(layout)
    
    def update_display(self):
        if self.show_full_file:
            self.show_full_files()
        else:
            self.show_diff_only()
    
    def show_full_files(self):
        # Display full files with highlighting
        local_lines = self.local_content.splitlines()
        commit_lines = self.commit_content.splitlines()
        
        # Create unified diff to identify changes
        diff = list(difflib.unified_diff(commit_lines, local_lines, lineterm=''))
        
        # Parse diff to identify changed lines
        local_changes = set()
        commit_changes = set()
        
        local_line_num = 0
        commit_line_num = 0
        
        for line in diff:
            if line.startswith('@@'):
                # Parse line numbers from diff header
                match = re.search(r'-(?P<commit_start>\d+)(?:,(?P<commit_count>\d+))? \+(?P<local_start>\d+)(?:,(?P<local_count>\d+))?', line)
                if match:
                    commit_line_num = int(match.group('commit_start')) - 1
                    local_line_num = int(match.group('local_start')) - 1
            elif line.startswith('-'):
                commit_changes.add(commit_line_num)
                commit_line_num += 1
            elif line.startswith('+'):
                local_changes.add(local_line_num)
                local_line_num += 1
            elif line.startswith(' '):
                commit_line_num += 1
                local_line_num += 1
        
        # Display local file with highlighting
        self.local_text.clear()
        for i, line in enumerate(local_lines):
            if i in local_changes:
                self.local_text.setTextColor(QColor(129, 199, 132))  # Bright green for changes
                self.local_text.append(f"{i+1:4d}: {line}")
            else:
                self.local_text.setTextColor(QColor(255, 255, 255))  # White for unchanged
                self.local_text.append(f"{i+1:4d}: {line}")
        
        # Display commit file with highlighting
        self.commit_text.clear()
        for i, line in enumerate(commit_lines):
            if i in commit_changes:
                self.commit_text.setTextColor(QColor(239, 83, 80))  # Bright red for changes
                self.commit_text.append(f"{i+1:4d}: {line}")
            else:
                self.commit_text.setTextColor(QColor(255, 255, 255))  # White for unchanged
                self.commit_text.append(f"{i+1:4d}: {line}")
    
    def show_diff_only(self):
        # Show only the differences
        local_lines = self.local_content.splitlines()
        commit_lines = self.commit_content.splitlines()
        
        diff = list(difflib.unified_diff(commit_lines, local_lines, 
                                       fromfile=f"Commit {self.commit_hash[:8]}",
                                       tofile="Local File",
                                       lineterm=''))
        
        # Display diff in left panel
        self.local_text.clear()
        for line in diff:
            if line.startswith('+++') or line.startswith('---'):
                self.local_text.setTextColor(QColor(255, 255, 255))
                self.local_text.append(line)
            elif line.startswith('@@'):
                self.local_text.setTextColor(QColor(100, 181, 246))  # Blue for context
                self.local_text.append(line)
            elif line.startswith('-'):
                self.local_text.setTextColor(QColor(239, 83, 80))  # Red for removed
                self.local_text.append(line)
            elif line.startswith('+'):
                self.local_text.setTextColor(QColor(129, 199, 132))  # Green for added
                self.local_text.append(line)
            else:
                self.local_text.setTextColor(QColor(255, 255, 255))
                self.local_text.append(line)
        
        # Show instructions in right panel
        self.commit_text.clear()
        self.commit_text.setTextColor(QColor(255, 255, 255))
        self.commit_text.append("📋 Unified Diff Legend:")
        self.commit_text.append("")
        self.commit_text.setTextColor(QColor(239, 83, 80))
        self.commit_text.append("- Lines removed from commit")
        self.commit_text.setTextColor(QColor(129, 199, 132))
        self.commit_text.append("+ Lines added to local file")
        self.commit_text.setTextColor(QColor(100, 181, 246))
        self.commit_text.append("@@ Line number context")
        self.commit_text.setTextColor(QColor(255, 255, 255))
        self.commit_text.append("")
        self.commit_text.append("Click 'Show Full Files' to see side-by-side comparison")
        self.commit_text.append("")
        self.commit_text.append("🔍 The left panel shows the unified diff")
        self.commit_text.append("🗂️ Use this view to focus on changes only")
    
    def toggle_view(self):
        self.show_full_file = not self.show_full_file
        self.toggle_view_button.setText("Show Diff Only" if self.show_full_file else "Show Full Files")
        self.update_display()
    
    def sync_scroll_left_fullscreen(self, value):
        """Sync scrolling from commit text to local text in fullscreen"""
        if hasattr(self, '_syncing_scroll_fs') and self._syncing_scroll_fs:
            return
        self._syncing_scroll_fs = True
        self.local_text.verticalScrollBar().setValue(value)
        self._syncing_scroll_fs = False
    
    def sync_scroll_right_fullscreen(self, value):
        """Sync scrolling from local text to commit text in fullscreen"""
        if hasattr(self, '_syncing_scroll_fs') and self._syncing_scroll_fs:
            return
        self._syncing_scroll_fs = True
        self.commit_text.verticalScrollBar().setValue(value)
        self._syncing_scroll_fs = False
    
    def keyPressEvent(self, event):
        # ESC key to close
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GitTimeTravel()
    window.show()
    sys.exit(app.exec())
