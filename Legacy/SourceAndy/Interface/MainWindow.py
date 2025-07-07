# File: MainWindow.py
# Path: Source/Interface/MainWindow.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-06
# Last Modified: 2025-07-06  03:42PM
"""
Description: Main Application Window for Anderson's Library - FIXED PySide6 Imports
Orchestrates all UI components and provides the main application interface.
CRITICAL FIX: Corrected PyQt syntax errors to proper PySide6 Signal imports.

Features:
- Component orchestration and lifecycle management
- Event routing between filter panel and book grid
- Status bar with statistics and progress indication
- Menu system and toolbar integration
- Theme and styling management
- Window state persistence
- Error handling and user feedback

Dependencies:
- PySide6: Qt framework for GUI components (CORRECTED IMPORTS)
- Source.Core.DatabaseManager: Database operations
- Source.Core.BookService: Business logic
- Source.Interface.FilterPanel: Left sidebar filters
- Source.Interface.BookGrid: Main book display
- logging: Application logging
"""

import sys
import logging
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QFrame, QStatusBar, QMessageBox, QSplitter, QMenuBar, QMenu,
    QProgressBar, QLabel, QToolBar, QPushButton
)
from PySide6.QtCore import Qt, QTimer, Signal  # ✅ FIXED: Signal not pyqtSignal
from PySide6.QtGui import QFont, QIcon, QAction, QPixmap

from Source.Core.DatabaseManager import DatabaseManager
from Source.Core.BookService import BookService
from Source.Interface.FilterPanel import FilterPanel
from Source.Interface.BookGrid import BookGrid
from Source.Utils.AboutDialog import AboutDialog


class MainWindow(QMainWindow):
    """
    Main application window for Anderson's Library.
    
    Coordinates all UI components and provides the primary user interface.
    Handles application lifecycle, event routing, and user interactions.
    """
    
    # ✅ FIXED: Using Signal instead of pyqtSignal
    BookSelected = Signal(dict)  # Emitted when a book is selected
    FiltersChanged = Signal(dict)  # Emitted when filters change
    StatusUpdated = Signal(str)  # Emitted when status should update
    
    def __init__(self):
        """Initialize the main window and all components."""
        super().__init__()
        
        # Setup logging
        self.Logger = logging.getLogger(self.__class__.__name__)
        
        # Core components
        self.DatabaseManager: Optional[DatabaseManager] = None
        self.BookService: Optional[BookService] = None
        
        # UI components
        self.FilterPanel: Optional[FilterPanel] = None
        self.BookGrid: Optional[BookGrid] = None
        self.CentralWidget: Optional[QWidget] = None
        self.MainSplitter: Optional[QSplitter] = None
        self.StatusBar: Optional[QStatusBar] = None
        self.ProgressBar: Optional[QProgressBar] = None
        self.StatusLabel: Optional[QLabel] = None
        
        # State management
        self.CurrentBooks: List[Dict[str, Any]] = []
        self.IsLoading: bool = False
        self.LastFilterCriteria: Dict[str, Any] = {}
        
        # Initialize application
        self.InitializeComponents()
        self.SetupUI()
        self.ApplyTheme()
        self.ConnectSignals()
        self.LoadInitialData() # Ensure initial data is loaded after setup
        
        self.Logger.info("MainWindow initialized successfully")
    
    def InitializeComponents(self) -> None:
        """Initialize core application components."""
        try:
            # Initialize database manager
            self.DatabaseManager = DatabaseManager("Data/Databases/MyLibrary.db")
            
            # Connect to database
            if not self.DatabaseManager.Connect():
                self.ShowCriticalError("Database connection failed")
                return
            
            # Initialize book service
            self.BookService = BookService(self.DatabaseManager)
            
            # Initialize UI components
            self.FilterPanel = FilterPanel(self.BookService)
            self.BookGrid = BookGrid(self.BookService)
            
            self.Logger.info("Core components initialized successfully")
            
        except Exception as Error:
            self.Logger.critical(f"Failed to initialize components: {Error}")
            self.ShowCriticalError(f"Failed to initialize application: {Error}")
    
    def SetupUI(self) -> None:
        """Setup the user interface layout and components."""
        try:
            # Set window properties
            self.setWindowTitle("Anderson's Library - Professional Edition")
            self.resize(1600, 1000)
            
            # Create menu bar
            self.CreateMenuBar()
            
            
            
            # Create central widget
            self.CentralWidget = QWidget()
            self.setCentralWidget(self.CentralWidget)
            
            # Create main layout with splitter
            MainLayout = QHBoxLayout(self.CentralWidget)
            MainLayout.setContentsMargins(8, 8, 8, 8)
            MainLayout.setSpacing(8)
            
            # Create splitter for resizable panels
            self.MainSplitter = QSplitter(Qt.Orientation.Horizontal)
            MainLayout.addWidget(self.MainSplitter)
            
            # Add filter panel (left side)
            if self.FilterPanel:
                self.FilterPanel.setMaximumWidth(350)
                self.FilterPanel.setMinimumWidth(250)
                self.MainSplitter.addWidget(self.FilterPanel)
            
            # Add book grid (right side)
            if self.BookGrid:
                self.MainSplitter.addWidget(self.BookGrid)
            
            # Set splitter proportions (25% filter, 75% books)
            self.MainSplitter.setSizes([300, 1200])
            
            # Create status bar
            self.CreateStatusBar()
            
            self.Logger.debug("UI layout setup completed")
            
        except Exception as Error:
            self.Logger.error(f"Failed to setup UI: {Error}")
            self.ShowError(f"UI setup failed: {Error}")
    
    def CreateMenuBar(self) -> None:
        """Create the application menu bar."""
        try:
            MenuBar = self.menuBar()
            
            # File menu
            FileMenu = MenuBar.addMenu("&File")
            
            RefreshAction = QAction("&Refresh Library", self)
            RefreshAction.setShortcut("F5")
            RefreshAction.triggered.connect(self.RefreshLibrary)
            FileMenu.addAction(RefreshAction)
            
            FileMenu.addSeparator()
            
            ExitAction = QAction("E&xit", self)
            ExitAction.setShortcut("Ctrl+Q")
            ExitAction.triggered.connect(self.close)
            FileMenu.addAction(ExitAction)
            
            # View menu
            ViewMenu = MenuBar.addMenu("&View")
            
            GridViewAction = QAction("&Grid View", self)
            GridViewAction.triggered.connect(lambda: self.SetViewMode("grid"))
            ViewMenu.addAction(GridViewAction)
            
            ListViewAction = QAction("&List View", self)
            ListViewAction.triggered.connect(lambda: self.SetViewMode("list"))
            ViewMenu.addAction(ListViewAction)
            
            # Tools menu
            ToolsMenu = MenuBar.addMenu("&Tools")
            
            StatsAction = QAction("Database &Statistics", self)
            StatsAction.triggered.connect(self.ShowDatabaseStats)
            ToolsMenu.addAction(StatsAction)
            
            # Help menu
            HelpMenu = MenuBar.addMenu("&Help")
            
            AboutAction = QAction("&About", self)
            AboutAction.triggered.connect(self.ShowAbout)
            HelpMenu.addAction(AboutAction)
            
            self.Logger.debug("Menu bar created successfully")
            
        except Exception as Error:
            self.Logger.error(f"Failed to create menu bar: {Error}")
    
    
    
    def CreateStatusBar(self) -> None:
        """Create and configure the status bar."""
        try:
            self.StatusBar = self.statusBar()
            
            # Main status label
            self.StatusLabel = QLabel("Ready")
            self.StatusBar.addWidget(self.StatusLabel)
            
            # Progress bar (hidden by default)
            self.ProgressBar = QProgressBar()
            self.ProgressBar.setVisible(False)
            self.ProgressBar.setMaximumWidth(200)
            self.StatusBar.addPermanentWidget(self.ProgressBar)
            
            # Database stats label
            self.DatabaseStatsLabel = QLabel("")
            self.StatusBar.addPermanentWidget(self.DatabaseStatsLabel)
            
            self.Logger.debug("Status bar created successfully")
            
        except Exception as Error:
            self.Logger.error(f"Failed to create status bar: {Error}")
    
    def ConnectSignals(self) -> None:
        """Connect signals between components."""
        try:
            if not self.FilterPanel or not self.BookGrid:
                self.Logger.warning("Components not available for signal connection")
                return
            
            # Filter panel signals
            self.FilterPanel.FiltersChanged.connect(self.OnFiltersChanged)
            self.FilterPanel.SearchRequested.connect(self.OnSearchRequested)
            self.FilterPanel.ViewModeChanged.connect(self.SetViewMode)
            self.FilterPanel.SubjectsUpdated.connect(self.UpdateDatabaseStats)
            
            # Book grid signals
            self.BookGrid.BookSelected.connect(self.OnBookSelected)
            self.BookGrid.BookOpened.connect(self.OnBookOpened)
            self.BookGrid.SelectionChanged.connect(self.OnSelectionChanged)
            
            # Internal signals
            self.StatusUpdated.connect(self.UpdateStatusBar)
            
            self.Logger.debug("Component signals connected successfully")
            
        except Exception as Error:
            self.Logger.error(f"Failed to connect signals: {Error}")
    
    
    
    def ApplyTheme(self) -> None:
        """Apply the application theme and styling."""
        try:
            # Set application font
            Font = QFont("Segoe UI", 9)
            self.setFont(Font)
            
            # Apply modern dark theme
            self.setStyleSheet("""
                QMainWindow {
                    background-color: qlineargradient(
                        spread:repeat, x1:1, y1:0, x2:1, y2:1, 
                        stop:0.00480769 rgba(3, 50, 76, 255), 
                        stop:0.293269 rgba(6, 82, 125, 255), 
                        stop:0.514423 rgba(8, 117, 178, 255), 
                        stop:0.745192 rgba(7, 108, 164, 255), 
                        stop:1 rgba(3, 51, 77, 255)
                    );
                    color: #ffffff;
                }
                
                QMenuBar {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: none;
                    padding: 4px;
                }
                
                QMenuBar::item {
                    background-color: transparent;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                
                QMenuBar::item:selected {
                    background-color: #0078d4;
                }
                
                QMenu {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 4px;
                }
                
                QMenu::item {
                    padding: 6px 20px;
                    border-radius: 4px;
                }
                
                QMenu::item:selected {
                    background-color: #0078d4;
                }
                
                QToolBar {
                    background-color: #3c3c3c;
                    border: none;
                    spacing: 4px;
                    padding: 4px;
                }
                
                QPushButton {
                    background-color: #0078d4;
                    color: #ffffff;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: 500;
                }
                
                QPushButton:hover {
                    background-color: #106ebe;
                }
                
                QPushButton:pressed {
                    background-color: #005a9e;
                }
                
                QStatusBar {
                    background-color: #FF0000;
                    color: #ffffff;
                    border-top: 1px solid #555555;
                }
                
                QProgressBar {
                    border: 1px solid #555555;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                
                QProgressBar::chunk {
                    background-color: #0078d4;
                    border-radius: 3px;
                }
                
                QSplitter::handle {
                    background-color: #555555;
                    width: 2px;
                }
                
                QSplitter::handle:hover {
                    background-color: #0078d4;
                }
                QToolTip { 
                    color: #ffffff; 
                    background-color: #3c3c3c; 
                    border: 1px solid #555555; 
                    font-size: 16px; 
                }
            """)
            
            self.Logger.debug("Theme applied successfully")
            
        except Exception as Error:
            self.Logger.error(f"Failed to apply theme: {Error}")
    
    def LoadInitialData(self) -> None:
        """Load initial data when application starts."""
        try:
            # Force re-parsing of this method
            if self.BookGrid:
                self.BookGrid.SetBooks([])
            self.UpdateDatabaseStats()
            
        except Exception as Error:
            self.Logger.error(f"Failed to load initial data: {Error}")
            self.HideProgress()
            self.UpdateStatusBar("Failed to load library")
    
    def LoadAllBooks(self) -> None:
        """Load all books and display them."""
        try:
            if not self.BookService:
                self.Logger.error("BookService not available")
                return
            
            # Get all books
            self.CurrentBooks = self.BookService.GetAllBooks()
            
            # Update book grid
            if self.BookGrid:
                self.BookGrid.SetBooks(self.CurrentBooks)
            
            # Update status
            BookCount = len(self.CurrentBooks)
            self.UpdateStatusBar(f"Showing all books: {BookCount} books")
            self.UpdateDatabaseStats()
            
            self.HideProgress()
            self.Logger.info(f"Loaded {BookCount} books successfully")
            
        except Exception as Error:
            self.Logger.error(f"Failed to load books: {Error}")
            self.HideProgress()
            self.UpdateStatusBar("Failed to load books")
            self.ShowError(f"Failed to load books: {Error}")
    
    def OnFiltersChanged(self, Criteria: Dict[str, Any]) -> None:
        """Handle filter changes from filter panel."""
        try:
            self.Logger.debug(f"Filters changed: {Criteria}")
            self.LastFilterCriteria = Criteria
            
            self.ShowProgress("Filtering books...")
            QTimer.singleShot(50, lambda: self.ApplyFilters(Criteria))
            
        except Exception as Error:
            self.Logger.error(f"Failed to handle filter change: {Error}")
            self.HideProgress()
    
    def ApplyFilters(self, Criteria: Dict[str, Any]) -> None:
        """Apply filters and update book display."""
        try:
            if not self.BookService:
                return
            
            # Extract filter criteria
            Category = Criteria.get('Category', '')
            Subject = Criteria.get('Subject', '')
            SearchTerm = Criteria.get('SearchTerm', '')
            
            # Get filtered books
            if SearchTerm:
                FilteredBooks = self.BookService.SearchBooks(SearchTerm)
            elif Category or Subject:
                FilteredBooks = self.BookService.GetBooksByFilters(Category, Subject)
            else:
                FilteredBooks = self.BookService.GetAllBooks()
            
            # Update current books
            self.CurrentBooks = FilteredBooks
            
            # Update book grid
            if self.BookGrid:
                self.BookGrid.SetBooks(self.CurrentBooks)
            
            # Update status
            self.UpdateFilterStatus(Criteria, len(FilteredBooks))
            self.HideProgress()
            self.UpdateDatabaseStats()
            
            self.Logger.debug(f"Applied filters, showing {len(FilteredBooks)} books")
            
        except Exception as Error:
            self.Logger.error(f"Failed to apply filters: {Error}")
            self.HideProgress()
            self.UpdateStatusBar("Filter operation failed")
    
    def OnSearchRequested(self, SearchTerm: str) -> None:
        """Handle search request from filter panel."""
        try:
            if not SearchTerm.strip():
                self.LoadAllBooks()
                return
            
            self.ShowProgress(f"Searching for '{SearchTerm}'...")
            Criteria = {'SearchTerm': SearchTerm}
            QTimer.singleShot(50, lambda: self.ApplyFilters(Criteria))
            
        except Exception as Error:
            self.Logger.error(f"Failed to handle search request: {Error}")
            self.HideProgress()
    
    def OnResetRequested(self) -> None:
        """Handle reset request from filter panel."""
        try:
            self.ShowProgress("Resetting filters...")
            self.LastFilterCriteria = {}
            QTimer.singleShot(50, self.LoadAllBooks)
            
        except Exception as Error:
            self.Logger.error(f"Failed to handle reset request: {Error}")
            self.HideProgress()
    
    def OnBookSelected(self, Book: Dict[str, Any]) -> None:
        """Handle book selection from book grid."""
        try:
            self.Logger.debug(f"Book selected: {Book.get('Title', 'Unknown')}")
            self.BookSelected.emit(Book)
            
        except Exception as Error:
            self.Logger.error(f"Failed to handle book selection: {Error}")
    
    def OnBookOpened(self, Book: Dict[str, Any]) -> None:
        """Handle book opening from book grid."""
        try:
            BookTitle = Book.get('Title', 'Unknown')
            self.Logger.info(f"Opening book: {BookTitle}")
            
            if self.BookService:
                Success = self.BookService.OpenBook(BookTitle)
                if Success:
                    self.UpdateStatusBar(f"Opened: {BookTitle}")
                else:
                    self.ShowError(f"Failed to open book: {BookTitle}")
            
        except Exception as Error:
            self.Logger.error(f"Failed to handle book opening: {Error}")
            self.ShowError(f"Failed to open book: {Error}")
    
    def OnSelectionChanged(self, Count: int) -> None:
        """Handle selection change in book grid."""
        try:
            if Count == 0:
                self.UpdateStatusBar("No books selected")
            elif Count == 1:
                self.UpdateStatusBar("1 book selected")
            else:
                self.UpdateStatusBar(f"{Count} books selected")
                
        except Exception as Error:
            self.Logger.error(f"Failed to handle selection change: {Error}")
    
    def RefreshLibrary(self) -> None:
        """Refresh the entire library display."""
        try:
            self.Logger.info("Refreshing library")
            
            # Clear caches
            if self.BookService:
                self.BookService.ClearCache()
            
            # Refresh filter panel
            if self.FilterPanel:
                self.FilterPanel.RefreshData()
            
            # Reload books
            self.LoadAllBooks()
            
        except Exception as Error:
            self.Logger.error(f"Failed to refresh library: {Error}")
            self.ShowError(f"Failed to refresh library: {Error}")
    
    def SetViewMode(self, Mode: str) -> None:
        """Set the view mode for book display."""
        try:
            if self.BookGrid:
                self.BookGrid.SetViewMode(Mode)
                self.UpdateStatusBar(f"View mode: {Mode}")
                
        except Exception as Error:
            self.Logger.error(f"Failed to set view mode: {Error}")
    
    def ShowDatabaseStats(self) -> None:
        """Show database statistics dialog."""
        try:
            if not self.BookService:
                return
            
            Stats = self.BookService.GetDatabaseStats()
            Message = f"""Database Statistics:
            
Books: {Stats.get('Books', 0)}
Categories: {Stats.get('Categories', 0)}
Subjects: {Stats.get('Subjects', 0)}
            
Current Display: {len(self.CurrentBooks)} books"""
            
            QMessageBox.information(self, "Database Statistics", Message)
            
        except Exception as Error:
            self.Logger.error(f"Failed to show database stats: {Error}")
    
    def ShowAbout(self) -> None:
        """Show about dialog."""
        try:
            about_dialog = AboutDialog(self)
            about_dialog.exec()
            
        except Exception as Error:
            self.Logger.error(f"Failed to show about dialog: {Error}")
    
    def UpdateFilterStatus(self, Criteria: Dict[str, Any], ResultCount: int) -> None:
        """Update status bar with filter information."""
        try:
            if not Criteria:
                self.UpdateStatusBar(f"Showing all books: {ResultCount} books")
                return
            
            FilterParts = []
            
            if Criteria.get('SearchTerm'):
                FilterParts.append(f"Search: '{Criteria['SearchTerm']}'")
            if Criteria.get('Category'):
                FilterParts.append(f"Category: {Criteria['Category']}")
            if Criteria.get('Subject'):
                FilterParts.append(f"Subject: {Criteria['Subject']}")
            
            if FilterParts:
                FilterText = " | ".join(FilterParts)
                self.UpdateStatusBar(f"Filtered ({FilterText}): {ResultCount} books")
            else:
                self.UpdateStatusBar(f"Showing all books: {ResultCount} books")
                
        except Exception as Error:
            self.Logger.error(f"Failed to update filter status: {Error}")
    
    def UpdateDatabaseStats(self) -> None:
        """Update database statistics in status bar."""
        try:
            if not self.BookService or not hasattr(self, 'DatabaseStatsLabel'):
                return
            
            Stats = self.BookService.GetDatabaseStats()
            
            TotalBooksCount = Stats.get('Books', 0) # Total books in DB
            DisplayedBooksCount = len(self.CurrentBooks) # Books currently displayed

            # Get current subjects in dropdown from FilterPanel
            SubjectsInDropdown = 0
            if self.FilterPanel and self.FilterPanel.SubjectComboBox:
                SubjectsInDropdown = self.FilterPanel.SubjectComboBox.count() - 1 # Exclude "All Subjects"

            # Determine which total to display
            if DisplayedBooksCount > 0:
                DisplayTotal = DisplayedBooksCount
            else:
                DisplayTotal = TotalBooksCount

            StatsText = f"<span style=\"color: #FFFFFF;\">{Stats.get('Categories', 0)}</span> <span style=\"color: #FFFF00;\">Categories</span>&nbsp;&nbsp;<span style=\"color: #FFFFFF;\">{SubjectsInDropdown}</span> <span style=\"color: #FFFF00;\">Subjects</span>&nbsp;&nbsp;<span style=\"color: #FFFFFF;\">{DisplayTotal}</span> <span style=\"color: #FFFF00;\">Total eBooks</span>"
            self.DatabaseStatsLabel.setText(StatsText)
            
        except Exception as Error:
            self.Logger.error(f"Failed to update database stats: {Error}")
    
    def ShowProgress(self, Message: str) -> None:
        """Show progress indication."""
        try:
            if self.ProgressBar and self.StatusLabel:
                self.StatusLabel.setText(Message)
                self.ProgressBar.setVisible(True)
                self.ProgressBar.setRange(0, 0)  # Indeterminate progress
                self.IsLoading = True
                
        except Exception as Error:
            self.Logger.error(f"Failed to show progress: {Error}")
    
    def HideProgress(self) -> None:
        """Hide progress indication."""
        try:
            if self.ProgressBar:
                self.ProgressBar.setVisible(False)
                self.IsLoading = False
                
        except Exception as Error:
            self.Logger.error(f"Failed to hide progress: {Error}")
    
    def UpdateStatusBar(self, Message: str) -> None:
        """Update status bar message."""
        try:
            if self.StatusLabel and not self.IsLoading:
                self.StatusLabel.setText(Message)
                
        except Exception as Error:
            self.Logger.error(f"Failed to update status bar: {Error}")
    
    def ShowError(self, Message: str) -> None:
        """Show error message to user."""
        try:
            QMessageBox.critical(self, "Error", Message)
        except Exception as Error:
            self.Logger.error(f"Failed to show error dialog: {Error}")
    
    def ShowCriticalError(self, Message: str) -> None:
        """Show critical error and exit application."""
        try:
            QMessageBox.critical(self, "Critical Error", 
                               f"{Message}\n\nThe application will now exit.")
            sys.exit(1)
        except Exception as Error:
            self.Logger.critical(f"Critical error in error handling: {Error}")
            sys.exit(1)
    
    def closeEvent(self, Event) -> None:
        """Handle application close event."""
        try:
            self.Logger.info("Application closing")
            
            # Close database connection
            if self.DatabaseManager:
                self.DatabaseManager.Close()
            
            Event.accept()
            
        except Exception as Error:
            self.Logger.error(f"Error during application close: {Error}")
            Event.accept()

if __name__ == "__main__":
    sys.exit(RunApplication())