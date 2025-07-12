import os
import subprocess
import datetime
import sys
import webbrowser
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QListWidget,
    QPushButton, QMessageBox, QHBoxLayout
)

class GitTimeTravel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🕰️ Himalaya Git Time Travel Console")
        self.setMinimumWidth(720)
        self.repo_name = os.path.basename(os.getcwd())
        self.github_user = "CallMeChewy"
        self.repo_url = f"https://github.com/{self.github_user}/{self.repo_name}"
        self.init_ui()
        self.populate_commits()

    def init_ui(self):
        layout = QVBoxLayout()

        self.status_label = QLabel("🔍 Verifying Git status...")
        layout.addWidget(self.status_label)

        self.repo_link = QPushButton(f"📎 View {self.repo_name} on GitHub")
        self.repo_link.clicked.connect(self.open_repo_url)
        layout.addWidget(self.repo_link)

        self.commit_list = QListWidget()
        layout.addWidget(self.commit_list)

        button_layout = QHBoxLayout()
        self.travel_button = QPushButton("🧭 Travel to Selected Commit")
        self.travel_button.clicked.connect(self.travel_to_commit)
        button_layout.addWidget(self.travel_button)

        self.exit_button = QPushButton("❌ Exit")
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.exit_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def open_repo_url(self):
        webbrowser.open(self.repo_url)

    def populate_commits(self):
        try:
            self.current_branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                text=True
            ).strip()

            self.status_label.setText(f"📍 Current Branch: {self.current_branch}")

            raw_logs = subprocess.check_output([
                "git", "log", "--pretty=format:%H|%h %ad %s",
                "--date=short", "-n", "30"
            ], text=True).splitlines()

            self.commits = []
            for line in raw_logs:
                full_hash, desc = line.split("|", 1)
                self.commits.append((full_hash.strip(), desc.strip()))
                self.commit_list.addItem(desc.strip())
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Git Error", "❌ Not a Git repository or Git not found.")
            self.close()

    def travel_to_commit(self):
        index = self.commit_list.currentRow()
        if index < 0:
            QMessageBox.warning(self, "No Selection", "⚠️ Please select a commit from the list.")
            return

        commit_hash, desc = self.commits[index]

        answer = QMessageBox.question(
            self,
            "Checkout Confirmation",
            f"🧭 Travel to:\n\n{desc}\n\nCreate a temporary branch?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )

        if answer == QMessageBox.Cancel:
            return

        try:
            if answer == QMessageBox.Yes:
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
                f"{msg}\n\nTo return to your branch:\n  git switch {self.current_branch}\n\n"
                f"📎 View this commit online:\n  {self.repo_url}/commit/{commit_hash}"
            )
            self.close()

        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Git Checkout Failed", f"❌ Error while switching:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GitTimeTravel()
    window.show()
    sys.exit(app.exec())
