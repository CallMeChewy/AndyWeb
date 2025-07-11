# TimeTraveiGitHub - User Guide

## Overview

TimeTraveiGitHub is a GUI application for Git repository time travel and file comparison. It provides an intuitive interface to explore commit history, compare files between commits, and temporarily switch to historical states.

## Features

### Core Functionality

- **Git Time Travel**: Navigate through commit history and temporarily switch to any commit
- **File Tracking**: Select specific files to track changes across commits
- **Visual Diff Comparison**: Side-by-side file comparison with syntax highlighting
- **Web File Focus**: Automatically filters and highlights web development files (.py, .js, .css, .html)
- **GitHub Integration**: Direct links to view commits on GitHub

### Interface Components

#### Main Window

- **Commit History List**: Shows last 30 commits with timestamps and descriptions
- **File Selection**: Button to select specific files for tracking
- **Diff View**: Real-time diff display for selected commits
- **Web Files Dropdown**: Shows web development files changed in selected commits
- **Time Travel Controls**: Buttons to travel to commits and return to original state

#### File Comparison Window

- **Side-by-Side View**: Compare local file with commit version
- **Diff-Only Mode**: Show only changed lines for focused analysis
- **Fullscreen Mode**: Maximized view for detailed comparison
- **Synchronized Scrolling**: Both panels scroll together for easy comparison

## Usage Guide

### Basic Operations

1. **Launch the Application**
   
   ```bash
   python Scripts/System/TimeTraveiGitHub.py
   ```

2. **Select a File to Track** (Optional)
   
   - Click "Select File to Track" button
   - Choose any file from your repository
   - Commits containing changes to this file will be highlighted with 📝

3. **Navigate Commit History**
   
   - Select any commit from the list
   - View changes in the diff panel
   - Web files (.py, .js, .css, .html) appear in the dropdown

4. **Compare Files**
   
   - Select a commit and web file from dropdown
   - File comparison window opens automatically
   - Use "Full Files" vs "Diff Only" toggle for different views

5. **Time Travel to Commit**
   
   - Select desired commit
   - Click "Travel to Selected Commit"
   - Choose to create temporary branch or detached HEAD
   - Use "Return to Original Branch" to restore

### Advanced Features

#### File Comparison Views

- **Full Files Mode**: Shows complete files with highlighted changes
- **Diff Only Mode**: Shows only changed lines for focused analysis
- **Fullscreen Mode**: Press F11 or click ⛶ for maximum screen space

#### Keyboard Shortcuts

- **F11**: Toggle fullscreen in comparison window
- **ESC**: Exit fullscreen or close comparison window

#### Color Coding

- **Green**: Lines added/current version
- **Red**: Lines removed/historical version
- **Bold + 📝**: Commits containing changes to selected file

## Best Practices

### File Selection Strategy

- **Track Critical Files**: Select key configuration or main source files
- **Use Web File Dropdown**: Automatically filters relevant development files
- **Compare Before Changes**: Review historical implementations before modifications

### Time Travel Safety

- **Always Create Branch**: Choose "Yes" when prompted to create temporary branch
- **Stash Changes**: Tool automatically stashes uncommitted work
- **Return Promptly**: Use "Return to Original Branch" to restore normal state
- **Check Status**: Monitor current branch indicator in status bar

### Diff Analysis

- **Start with Diff-Only**: Focus on changes first, then view full context
- **Use Fullscreen**: Maximize screen space for complex comparisons
- **Sync Scrolling**: Both panels scroll together for easy line-by-line comparison

## Configuration Options

### Himalaya Config (.himalaya.json)

The application reads configuration from `.himalaya.json` in the repository root:

```json
{
  "github_user": "your-username",
  "repo_settings": {
    "default_branch": "main",
    "max_commits": 30
  }
}
```

### GitHub Integration

- **Auto-Detection**: Uses repository name and configured GitHub user
- **Direct Links**: Click repository button to view on GitHub
- **Commit URLs**: Time travel dialog includes GitHub commit links

## Troubleshooting

### Common Issues

- **"Not a Git repository"**: Ensure you're running from within a Git repository
- **Empty commit list**: Check if repository has commits (`git log`)
- **File not found**: Selected file may not exist in historical commit
- **Diff generation failed**: File may be binary or have encoding issues

### Performance Tips

- **Limit File Size**: Large files may slow comparison operations
- **Recent History**: Tool shows last 30 commits by default for performance
- **Close Unused Windows**: Multiple comparison windows consume memory

### Git Requirements

- **git-restore-mtime**: Optional tool for timestamp accuracy
  
  ```bash
  pip install git-restore-mtime
  ```
- **Git Version**: Requires Git 2.23+ for `git switch` command

## Security Considerations

### Safe Operations

- **Read-Only Analysis**: File comparison operations don't modify files
- **Stash Protection**: Uncommitted changes are automatically stashed
- **Branch Isolation**: Temporary branches prevent accidental changes

### Caution Areas

- **Time Travel**: Creates temporary branches - always return to original
- **File Access**: Tool reads repository files but doesn't execute code
- **GitHub Links**: External links open in default browser

## Command Line Usage

### Basic Launch

```bash
python Scripts/System/TimeTraveiGitHub.py
```

### Prerequisites

- Python 3.6+
- PySide6 (PyQt6 alternative)
- Git repository context

### Dependencies

```bash
pip install PySide6
```

## Integration with Development Workflow

### Code Review Process

1. Use before implementing features to understand historical context
2. Compare current implementation with previous versions
3. Identify patterns in code evolution

### Debugging Historical Issues

1. Select problematic file for tracking
2. Navigate to commits where issue was introduced
3. Use diff view to understand changes
4. Time travel to test historical states

### Documentation and Learning

1. Track configuration files to understand setup evolution
2. Compare API implementations across versions
3. Study commit patterns for team development practices