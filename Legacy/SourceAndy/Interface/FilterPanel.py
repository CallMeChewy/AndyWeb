# File: FilterPanel.py
# Path: Source/Interface/FilterPanel.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-06
# Last Modified: 2025-07-06  02:57PM
"""
Description: Filter Panel for Anderson's Library - Left Sidebar Interface
Provides search and filtering interface for book library navigation.
Handles category/subject hierarchical filtering and text search.

Features:
- Hierarchical category and subject filtering
- Real-time text search with field selection
- Advanced filtering options (rating, file size, etc.)
- Filter state management and persistence
- Responsive UI with proper error handling
- Signal-based communication with main window

Dependencies:
- PySide6: Qt framework for GUI components
- Source.Core.BookService: Business logic for filtering
- Source.Data.DatabaseModels: Data models and search criteria
- logging: Application logging

Architecture:
- Signal-slot pattern for loose coupling
- State management for filter persistence
- Hierarchical data binding for category/subject relationships
- Responsive design with proper error handling
"""

import logging
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QFrame, QGroupBox, QSpinBox,
    QCheckBox, QSlider, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QIcon

from Source.Core.BookService import BookService
from Source.Data.DatabaseModels import SearchCriteria


class FilterPanel(QWidget):
    """
    Filter panel widget for book library filtering and search.
    
    Provides intuitive interface for:
    - Category and subject hierarchical filtering
    - Text search across multiple fields
    - Advanced filtering options
    - Filter state management
    """
    
    # Signals for communication with main window
    FiltersChanged = Signal(dict)  # Emitted when any filter changes
    SearchRequested = Signal(str)  # Emitted when search is performed
    CategoryChanged = Signal(str)  # Emitted when category selection changes
    SubjectChanged = Signal(str)  # Emitted when subject selection changes
    ViewModeChanged = Signal(str) # Emitted when the view mode changes
    SubjectsUpdated = Signal() # Emitted when the subjects dropdown is updated
    
    def __init__(self, BookService: BookService, parent=None):
        """
        Initialize filter panel with book service.
        
        Args:
            BookService: Business logic service for filtering operations
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        
        # Core dependencies
        self.BookService = BookService
        self.Logger = logging.getLogger(self.__class__.__name__)
        
        # UI components
        self.SearchLineEdit: Optional[QLineEdit] = None
        self.CategoryComboBox: Optional[QComboBox] = None
        self.SubjectComboBox: Optional[QComboBox] = None
        self.ResetButton: Optional[QPushButton] = None
        self.SearchButton: Optional[QPushButton] = None
        self.RatingSlider: Optional[QSlider] = None
        self.RatingLabel: Optional[QLabel] = None
        self.ThumbnailCheckBox: Optional[QCheckBox] = None
        
        # State management
        self.CurrentCategory: str = ""
        self.CurrentSubject: str = ""
        self.CurrentSearchTerm: str = ""
        self.IsUpdatingUI: bool = False
        
        # Timers for debounced search
        self.SearchTimer = QTimer()
        self.SearchTimer.setSingleShot(True)
        self.SearchTimer.timeout.connect(self.PerformSearch)
        
        # Initialize UI
        self.InitializeUI()
        self.LoadInitialData()
        self.ConnectSignals()
        self.ApplyStyles()
        
        self.Logger.info("FilterPanel initialized successfully")
    
    def InitializeUI(self) -> None:
        """Initialize the user interface components."""
        try:
            # Main layout
            MainLayout = QVBoxLayout(self)
            MainLayout.setContentsMargins(12, 12, 12, 12)
            MainLayout.setSpacing(16)

            # View mode buttons
            ViewModeLayout = self.CreateViewModeButtons()
            MainLayout.addLayout(ViewModeLayout)
            
            # Title
            TitleLabel = QLabel("--- Options ---")
            TitleLabel.setAlignment(Qt.AlignCenter)
            TitleLabel.setFont(QFont("Segoe UI", 11, QFont.Bold))
            MainLayout.addWidget(TitleLabel)
            
            # Search section
            SearchGroup = self.CreateSearchSection()
            MainLayout.addWidget(SearchGroup)
            
            # Filter section
            FilterGroup = self.CreateFilterSection()
            MainLayout.addWidget(FilterGroup)
            
            
            
            # Add stretch to push everything to top
            MainLayout.addStretch()
            
            self.Logger.debug("UI components initialized successfully")
            
        except Exception as Error:
            self.Logger.error(f"Failed to initialize UI: {Error}")
    
    def CreateSearchSection(self) -> QGroupBox:
        """Create the search input section."""
        try:
            SearchGroup = QGroupBox("Search")
            SearchLayout = QVBoxLayout(SearchGroup)
            SearchLayout.setSpacing(8)
            
            # Search label
            SearchLabel = QLabel("Search:")
            SearchLabel.setFont(QFont("Segoe UI", 9, QFont.Bold))
            SearchLayout.addWidget(SearchLabel)
            
            # Search input
            self.SearchLineEdit = QLineEdit()
            self.SearchLineEdit.setPlaceholderText("Type Something Here")
            self.SearchLineEdit.setMinimumHeight(32)
            SearchLayout.addWidget(self.SearchLineEdit)
            
            # Search button
            self.SearchButton = QPushButton("Search")
            self.SearchButton.setMinimumHeight(32)
            SearchLayout.addWidget(self.SearchButton)
            
            return SearchGroup
            
        except Exception as Error:
            self.Logger.error(f"Failed to create search section: {Error}")
            return QGroupBox()
    
    def CreateFilterSection(self) -> QGroupBox:
        """Create the category and subject filter section."""
        try:
            FilterGroup = QGroupBox("Filters")
            FilterLayout = QVBoxLayout(FilterGroup)
            FilterLayout.setSpacing(12)
            
            # Category section
            CategoryLabel = QLabel("Category:")
            CategoryLabel.setFont(QFont("Segoe UI", 9, QFont.Bold))
            FilterLayout.addWidget(CategoryLabel)
            
            self.CategoryComboBox = QComboBox()
            self.CategoryComboBox.setMinimumHeight(32)
            self.CategoryComboBox.addItem("All Categories")
            FilterLayout.addWidget(self.CategoryComboBox)
            
            # Subject section
            SubjectLabel = QLabel("Subject:")
            SubjectLabel.setFont(QFont("Segoe UI", 9, QFont.Bold))
            FilterLayout.addWidget(SubjectLabel)
            
            self.SubjectComboBox = QComboBox()
            self.SubjectComboBox.setMinimumHeight(32)
            self.SubjectComboBox.addItem("All Subjects")
            self.SubjectComboBox.setEnabled(False)  # Disabled until category selected
            FilterLayout.addWidget(self.SubjectComboBox)
            
            return FilterGroup
            
        except Exception as Error:
            self.Logger.error(f"Failed to create filter section: {Error}")
            return QGroupBox()
    
    def CreateViewModeButtons(self) -> QHBoxLayout:
        """Create the view mode buttons section."""
        try:
            ViewModeLayout = QHBoxLayout()
            ViewModeLayout.setSpacing(8)
            
            # Grid button
            self.GridButton = QPushButton("Grid")
            self.GridButton.setMinimumHeight(32)
            ViewModeLayout.addWidget(self.GridButton)

            # List button
            self.ListButton = QPushButton("List")
            self.ListButton.setMinimumHeight(32)
            ViewModeLayout.addWidget(self.ListButton)
            
            return ViewModeLayout
            
        except Exception as Error:
            self.Logger.error(f"Failed to create view mode buttons: {Error}")
            return QHBoxLayout()
    
    def LoadInitialData(self) -> None:
        """Load initial data for dropdowns."""
        try:
            self.IsUpdatingUI = True
            
            # Load categories
            Categories = self.BookService.GetCategories()
            if self.CategoryComboBox:
                self.CategoryComboBox.clear()
                self.CategoryComboBox.addItem("All Categories")
                for Category in Categories:
                    self.CategoryComboBox.addItem(Category)
            
            self.IsUpdatingUI = False
            
            self.Logger.info(f"Loaded {len(Categories)} categories")
            
        except Exception as Error:
            self.Logger.error(f"Failed to load initial data: {Error}")
            self.IsUpdatingUI = False
    
    def ConnectSignals(self) -> None:
        """Connect UI signals to handlers."""
        try:
            # Search signals
            if self.SearchLineEdit:
                self.SearchLineEdit.textChanged.connect(self.OnSearchTextChanged)
                self.SearchLineEdit.returnPressed.connect(self.OnSearchPressed)
            
            if self.SearchButton:
                self.SearchButton.clicked.connect(self.OnSearchPressed)
            
            # Filter signals
            if self.CategoryComboBox:
                self.CategoryComboBox.currentTextChanged.connect(self.OnCategoryChanged)
            
            if self.SubjectComboBox:
                self.SubjectComboBox.currentTextChanged.connect(self.OnSubjectChanged)
            
            # Advanced filter signals
            if self.RatingSlider:
                self.RatingSlider.valueChanged.connect(self.OnRatingChanged)
            
            if self.ThumbnailCheckBox:
                self.ThumbnailCheckBox.stateChanged.connect(self.OnThumbnailFilterChanged)

            if self.GridButton:
                self.GridButton.clicked.connect(lambda: self.ViewModeChanged.emit("grid"))

            if self.ListButton:
                self.ListButton.clicked.connect(lambda: self.ViewModeChanged.emit("list"))
            
            self.Logger.debug("UI signals connected successfully")
            
        except Exception as Error:
            self.Logger.error(f"Failed to connect signals: {Error}")
    
    def ApplyStyles(self) -> None:
        """Apply custom styles to the filter panel."""
        try:
            self.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #555555;
                    border-radius: 8px;
                    margin-top: 8px;
                    padding-top: 8px;
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    color: #0078d4;
                    font-size: 10pt;
                }
                
                QLabel {
                    color: #ffffff;
                    font-size: 9pt;
                }
                
                QLineEdit {
                    background-color: #2b2b2b;
                    border: 2px solid #555555;
                    border-radius: 6px;
                    padding: 6px;
                    color: #ffffff;
                    font-size: 9pt;
                }
                
                QLineEdit:focus {
                    border-color: #0078d4;
                }
                
                QComboBox {
                    background-color: #2b2b2b;
                    border: 2px solid #555555;
                    border-radius: 6px;
                    padding: 6px;
                    color: #ffffff;
                    font-size: 9pt;
                }
                
                QComboBox:focus {
                    border-color: #0078d4;
                }
                
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                
                QComboBox::down-arrow {
                    image: url(down_arrow.png);
                    width: 12px;
                    height: 12px;
                }
                
                QComboBox QAbstractItemView {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    selection-background-color: #0078d4;
                    border: 1px solid #555555;
                }
                
                QPushButton {
                    background-color: #4a4a4a;
                    color: #ffffff;
                    border: 2px solid #555555;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 500;
                    font-size: 9pt;
                }
                
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                
                QPushButton:pressed {
                    background-color: #3a3a3a;
                }
                
                QPushButton:disabled {
                    background-color: #555555;
                    color: #888888;
                }
                
                QSlider::groove:horizontal {
                    border: 1px solid #555555;
                    height: 6px;
                    background: #2b2b2b;
                    border-radius: 3px;
                }
                
                QSlider::handle:horizontal {
                    background: #0078d4;
                    border: 1px solid #0078d4;
                    width: 16px;
                    height: 16px;
                    border-radius: 8px;
                    margin: -5px 0;
                }
                
                QSlider::handle:horizontal:hover {
                    background: #106ebe;
                    border-color: #106ebe;
                }
                
                QCheckBox {
                    color: #ffffff;
                    font-size: 9pt;
                }
                
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 2px solid #555555;
                    border-radius: 3px;
                    background-color: #2b2b2b;
                }
                
                QCheckBox::indicator:checked {
                    background-color: #0078d4;
                    border-color: #0078d4;
                }
            """)
            
            self.Logger.debug("Styles applied successfully")
            
        except Exception as Error:
            self.Logger.error(f"Failed to apply styles: {Error}")
    
    def OnSearchTextChanged(self, Text: str) -> None:
        """Handle search text changes with debouncing."""
        try:
            if self.IsUpdatingUI:
                return
            
            # Debounce search to avoid excessive queries
            self.SearchTimer.stop()
            self.SearchTimer.start(500)  # 500ms delay
            
        except Exception as Error:
            self.Logger.error(f"Failed to handle search text change: {Error}")
    
    def OnSearchPressed(self) -> None:
        """Handle search button click or Enter press."""
        try:
            self.SearchTimer.stop()
            self.PerformSearch()
            
        except Exception as Error:
            self.Logger.error(f"Failed to handle search press: {Error}")
    
    def PerformSearch(self) -> None:
        """Perform the actual search operation."""
        try:
            if not self.SearchLineEdit:
                return
            
            SearchTerm = self.SearchLineEdit.text().strip()
            self.CurrentSearchTerm = SearchTerm
            
            if SearchTerm:
                self.Logger.debug(f"Performing search: '{SearchTerm}'")
                self.SearchRequested.emit(SearchTerm)
            else:
                # Empty search - apply current filters
                self.EmitFiltersChanged()
            
        except Exception as Error:
            self.Logger.error(f"Failed to perform search: {Error}")
    
    def OnCategoryChanged(self, Category: str) -> None:
        """Handle category selection change."""
        try:
            if self.IsUpdatingUI:
                return
            
            self.CurrentCategory = Category if Category != "All Categories" else ""
            self.Logger.debug(f"Category changed to: '{Category}'")
            
            # Update subjects for selected category
            self.UpdateSubjects(self.CurrentCategory)
            
            # Clear search and subject when category changes
            self.ClearSearch()
            if self.SubjectComboBox:
                self.SubjectComboBox.setCurrentIndex(0)
            
            # Emit category change signal
            self.CategoryChanged.emit(self.CurrentCategory)
            
            # Emit filters changed
            self.EmitFiltersChanged()
            
        except Exception as Error:
            self.Logger.error(f"Failed to handle category change: {Error}")
    
    def OnSubjectChanged(self, Subject: str) -> None:
        """Handle subject selection change."""
        try:
            if self.IsUpdatingUI:
                return
            
            self.CurrentSubject = Subject if Subject != "All Subjects" else ""
            self.Logger.debug(f"Subject changed to: '{Subject}'")
            
            # Clear search when filter changes
            self.ClearSearch()
            
            # Emit subject change signal
            self.SubjectChanged.emit(self.CurrentSubject)
            
            # Emit filters changed
            self.EmitFiltersChanged()
            
        except Exception as Error:
            self.Logger.error(f"Failed to handle subject change: {Error}")
    
    def OnRatingChanged(self, Rating: int) -> None:
        """Handle rating slider change."""
        try:
            if self.RatingLabel:
                self.RatingLabel.setText(str(Rating))
            
            if not self.IsUpdatingUI:
                self.EmitFiltersChanged()
                
        except Exception as Error:
            self.Logger.error(f"Failed to handle rating change: {Error}")
    
    def OnThumbnailFilterChanged(self, State: int) -> None:
        """Handle thumbnail filter checkbox change."""
        try:
            if not self.IsUpdatingUI:
                self.EmitFiltersChanged()
                
        except Exception as Error:
            self.Logger.error(f"Failed to handle thumbnail filter change: {Error}")
    
    def UpdateSubjects(self, Category: str) -> None:
        """Update subjects dropdown based on selected category."""
        try:
            if not self.SubjectComboBox:
                return
            
            self.IsUpdatingUI = True
            
            # Clear current subjects
            self.SubjectComboBox.clear()
            self.SubjectComboBox.addItem("All Subjects")
            
            if Category:
                # Load subjects for category
                Subjects = self.BookService.GetSubjectsForCategory(Category)
                for Subject in Subjects:
                    self.SubjectComboBox.addItem(Subject)
                
                self.SubjectComboBox.setEnabled(True)
                self.Logger.debug(f"Loaded {len(Subjects)} subjects for category '{Category}'")
            else:
                # No category selected
                self.SubjectComboBox.setEnabled(False)
            
            # Reset subject selection
            self.CurrentSubject = ""
            
            self.IsUpdatingUI = False
            self.SubjectsUpdated.emit()
            
        except Exception as Error:
            self.Logger.error(f"Failed to update subjects: {Error}")
            self.IsUpdatingUI = False
    
    def ClearSearch(self) -> None:
        """Clear the search field when filters change."""
        try:
            if self.SearchLineEdit and self.SearchLineEdit.text():
                self.IsUpdatingUI = True
                self.SearchLineEdit.clear()
                self.CurrentSearchTerm = ""
                self.IsUpdatingUI = False
                
        except Exception as Error:
            self.Logger.error(f"Failed to clear search: {Error}")
    
    def EmitFiltersChanged(self) -> None:
        """Emit filters changed signal with current criteria."""
        try:
            Criteria = self.GetCurrentCriteria()
            self.FiltersChanged.emit(Criteria)
            
        except Exception as Error:
            self.Logger.error(f"Failed to emit filters changed: {Error}")
    
    def GetCurrentCriteria(self) -> Dict[str, Any]:
        """Get current filter criteria as dictionary."""
        try:
            Criteria = {}
            
            # Search term
            if self.CurrentSearchTerm:
                Criteria['SearchTerm'] = self.CurrentSearchTerm
            
            # Category and subject
            if self.CurrentCategory:
                Criteria['Category'] = self.CurrentCategory
            
            if self.CurrentSubject:
                Criteria['Subject'] = self.CurrentSubject
            
            # Rating filter
            if self.RatingSlider and self.RatingSlider.value() > 0:
                Criteria['MinRating'] = self.RatingSlider.value()
            
            # Thumbnail filter
            if self.ThumbnailCheckBox and self.ThumbnailCheckBox.isChecked():
                Criteria['HasThumbnail'] = True
            
            return Criteria
            
        except Exception as Error:
            self.Logger.error(f"Failed to get current criteria: {Error}")
            return {}
    
    def RefreshData(self) -> None:
        """Refresh filter data from database."""
        try:
            self.Logger.info("Refreshing filter panel data")
            
            # Clear cache in book service
            self.BookService.ClearCache()
            
            # Reload categories
            self.LoadInitialData()
            
            # Reset to initial state
            self.OnResetClicked()
            
        except Exception as Error:
            self.Logger.error(f"Failed to refresh data: {Error}")
    
    def SetFilterCriteria(self, Criteria: Dict[str, Any]) -> None:
        """Set filter criteria programmatically."""
        try:
            self.IsUpdatingUI = True
            
            # Set search term
            SearchTerm = Criteria.get('SearchTerm', '')
            if self.SearchLineEdit:
                self.SearchLineEdit.setText(SearchTerm)
            self.CurrentSearchTerm = SearchTerm
            
            # Set category
            Category = Criteria.get('Category', '')
            if self.CategoryComboBox and Category:
                Index = self.CategoryComboBox.findText(Category)
                if Index >= 0:
                    self.CategoryComboBox.setCurrentIndex(Index)
            self.CurrentCategory = Category
            
            # Update subjects and set subject
            if Category:
                self.UpdateSubjects(Category)
            
            Subject = Criteria.get('Subject', '')
            if self.SubjectComboBox and Subject:
                Index = self.SubjectComboBox.findText(Subject)
                if Index >= 0:
                    self.SubjectComboBox.setCurrentIndex(Index)
            self.CurrentSubject = Subject
            
            # Set rating
            MinRating = Criteria.get('MinRating', 0)
            if self.RatingSlider:
                self.RatingSlider.setValue(MinRating)
            
            # Set thumbnail filter
            HasThumbnail = Criteria.get('HasThumbnail', False)
            if self.ThumbnailCheckBox:
                self.ThumbnailCheckBox.setChecked(HasThumbnail)
            
            self.IsUpdatingUI = False
            
            self.Logger.debug(f"Set filter criteria: {Criteria}")
            
        except Exception as Error:
            self.Logger.error(f"Failed to set filter criteria: {Error}")
            self.IsUpdatingUI = False