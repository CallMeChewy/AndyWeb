# File: BookGrid.py
# Path: Source/Interface/BookGrid.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-06
# Last Modified: 2025-07-06  11:26AM
"""
Description: Fixed Book Grid with Proper PySide6 Imports
Enhanced book display grid with proper imports and resize handling.
"""

import logging
import math
from typing import List, Dict, Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLabel,
    QPushButton, QGridLayout, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QPixmap, QFont, QPainter, QBrush, QColor

from Source.Core.BookService import BookService


class BookCard(QFrame):
    """
    Individual book card widget with enhanced styling.
    """
    
    BookClicked = Signal(dict)
    
    def __init__(self, BookData: dict, ViewMode: str = "grid"):
        super().__init__()
        
        self.BookData = BookData
        self.ViewMode = ViewMode
        self.Logger = logging.getLogger(__name__)
        
        # Set up the card
        self._SetupCard()
        self._LoadBookCover()
    
    def _SetupCard(self) -> None:
        """Setup the book card layout and styling"""
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        
        if self.ViewMode == "list":
            # List mode: horizontal layout with smaller icon
            self.setFixedSize(600, 80)
            Layout = QHBoxLayout(self)
            Layout.setContentsMargins(8, 2, 8, 2)
            Layout.setSpacing(10)
        else:
            # Grid mode: vertical layout with large icon
            self.setFixedSize(180, 280)
            Layout = QVBoxLayout(self)
            Layout.setContentsMargins(8, 8, 8, 8)
            Layout.setSpacing(5)
        
        # Cover image label
        self.CoverLabel = QLabel()
        self.CoverLabel.setAlignment(Qt.AlignCenter)
        
        if self.ViewMode == "list":
            # Small icon for list view
            self.CoverLabel.setMinimumSize(60, 60)
            self.CoverLabel.setMaximumSize(60, 60)
        else:
            # Large icon for grid view
            self.CoverLabel.setMinimumSize(160, 200)
            self.CoverLabel.setMaximumSize(160, 200)
            
        self.CoverLabel.setStyleSheet("""
            QLabel {
                border: 2px solid #4CAF50;
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 0.9);
                padding: 2px;
            }
        """)
        Layout.addWidget(self.CoverLabel)
        
        # Title label
        Title = self.BookData.get('Title', 'Unknown Title')
        if self.ViewMode == "list":
            # Full title for list view
            self.TitleLabel = QLabel(Title)
            self.TitleLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.TitleLabel.setWordWrap(True)
            self.TitleLabel.setStyleSheet("""
                QLabel {
                    color: #FFFFFF;
                    font-size: 14px;
                    font-weight: bold;
                    background-color: rgba(0, 0, 0, 0.7);
                    border-radius: 4px;
                    padding: 8px;
                }
            """)
        else:
            # Truncated title for grid view
            self.TitleLabel = QLabel(Title[:25] + "..." if len(Title) > 25 else Title)
            self.TitleLabel.setAlignment(Qt.AlignCenter)
            self.TitleLabel.setWordWrap(True)
            self.TitleLabel.setStyleSheet("""
                QLabel {
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: bold;
                    background-color: rgba(0, 0, 0, 0.7);
                    border-radius: 4px;
                    padding: 4px;
                }
            """)
        Layout.addWidget(self.TitleLabel)
        
        # Set hover effects
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border: 3px solid #FFC107;
            }
        """)
    
    def _LoadBookCover(self) -> None:
        """Load and display the book cover"""
        try:
            # Try to load cover from BLOB data first
            if 'ThumbnailData' in self.BookData and self.BookData['ThumbnailData']:
                Pixmap = QPixmap()
                if Pixmap.loadFromData(self.BookData['ThumbnailData']):
                    # Scale to fit the label based on view mode
                    if self.ViewMode == "list":
                        ScaledPixmap = Pixmap.scaled(
                            56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                    else:
                        ScaledPixmap = Pixmap.scaled(
                            156, 196, Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                    self.CoverLabel.setPixmap(ScaledPixmap)
                    return
                else:
                    self.Logger.warning(f"Failed to load thumbnail BLOB for book {self.BookData.get('ID', 'Unknown')}")
            
            # Fallback to file-based cover
            CoverPath = Path(f"Data/Covers/{self.BookData.get('ID', 0)}.jpg")
            if CoverPath.exists():
                Pixmap = QPixmap(str(CoverPath))
                if Pixmap.isNull():
                    self.Logger.warning(f"Failed to load file-based cover from {CoverPath} for book {self.BookData.get('ID', 'Unknown')}")
                if self.ViewMode == "list":
                    ScaledPixmap = Pixmap.scaled(
                        56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                else:
                    ScaledPixmap = Pixmap.scaled(
                        156, 196, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                self.CoverLabel.setPixmap(ScaledPixmap)
                return
            
            # No cover found - use placeholder
            self._CreatePlaceholder()
            
        except Exception as Error:
            self.Logger.error(f"Failed to load cover for book {self.BookData.get('ID', 'Unknown')}: {Error}")
            self._CreatePlaceholder()
    
    def _CreatePlaceholder(self) -> None:
        """Create a placeholder image for books without covers"""
        if self.ViewMode == "list":
            Placeholder = QPixmap(56, 56)
            FontSize = 8
            Text = "No\nCover"
        else:
            Placeholder = QPixmap(156, 196)
            FontSize = 12
            Text = "No Cover\nAvailable"
            
        Placeholder.fill(QColor("#E0E0E0"))
        
        # Draw placeholder text
        Painter = QPainter(Placeholder)
        Painter.setPen(QColor("#757575"))
        Font = QFont("Arial", FontSize, QFont.Bold)
        Painter.setFont(Font)
        Painter.drawText(Placeholder.rect(), Qt.AlignCenter, Text)
        Painter.end()
        
        self.CoverLabel.setPixmap(Placeholder)
    
    def mousePressEvent(self, event):
        """Handle mouse click on book card"""
        if event.button() == Qt.LeftButton:
            self.BookClicked.emit(self.BookData)
        super().mousePressEvent(event)


class BookGrid(QWidget):
    """
    Fixed book grid with proper PySide6 imports and enhanced functionality.
    
    Fixes applied:
    - Proper PySide6 Signal imports
    - Enhanced resize handling
    - Better grid calculations
    - Improved performance
    """
    
    BookSelected = Signal(dict)
    BookOpened = Signal(dict)
    SelectionChanged = Signal(int)
    
    def __init__(self, BookService: BookService):
        super().__init__()
        
        self.Logger = logging.getLogger(__name__)
        self.BookService = BookService
        
        # Current state
        self.CurrentBooks: List[Dict] = []
        self.CurrentFilters: Dict = {}
        self.BookCards: List[BookCard] = []
        
        # Layout settings
        self.ViewMode = "grid"
        self.ColumnsCount = 4
        self.CardWidth = 180
        self.CardHeight = 280
        
        # Initialize UI
        self._SetupUI()
        self._LoadAllBooks()
        
        self.Logger.info("Book grid initialized with fixes")
    
    def _SetupUI(self) -> None:
        """Setup the book grid user interface"""
        # Main layout
        MainLayout = QVBoxLayout(self)
        MainLayout.setContentsMargins(10, 10, 10, 10)
        MainLayout.setSpacing(5)
        
        # Create scroll area
        self.ScrollArea = QScrollArea()
        self.ScrollArea.setWidgetResizable(True)
        self.ScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.ScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        MainLayout.addWidget(self.ScrollArea)
        
        # Create scrollable content widget
        self.ContentWidget = QWidget()
        self.ScrollArea.setWidget(self.ContentWidget)

        # Add a label for the placeholder image
        self.PlaceholderLabel = QLabel(self.ContentWidget)
        self.PlaceholderLabel.setAlignment(Qt.AlignCenter)
        self.PlaceholderLabel.setPixmap(QPixmap("Assets/BowersWorld.png"))
        self.PlaceholderLabel.setVisible(False)
        
        # Create grid layout for book cards
        self.GridLayout = QGridLayout(self.ContentWidget)
        self.GridLayout.setVerticalSpacing(0)
        self.GridLayout.setHorizontalSpacing(15)
        self.GridLayout.setContentsMargins(10, 10, 10, 10)
        
        # Apply styling
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QScrollBar:vertical {
                background-color: rgba(255, 255, 255, 0.1);
                width: 16px;
                border-radius: 8px;
                margin: 0;
            }
            
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                min-height: 30px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: rgba(255, 255, 255, 0.5);
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
    
    def _LoadAllBooks(self) -> None:
        """Load all books from the database"""
        try:
            if self.BookService:
                self.CurrentBooks = self.BookService.GetAllBooks()
                self._UpdateDisplay()
                self.Logger.info(f"Loaded {len(self.CurrentBooks)} books")
            
        except Exception as Error:
            self.Logger.error(f"Failed to load books: {Error}")
    
    def _UpdateDisplay(self) -> None:
        """Update the book grid display"""
        try:
            # Clear existing cards
            self._ClearGrid()

            if not self.CurrentBooks:
                self.PlaceholderLabel.setVisible(True)
                return
            else:
                self.PlaceholderLabel.setVisible(False)
            
            # Calculate columns based on available width
            self._CalculateColumns()
            
            # Add book cards to grid
            Row, Col = 0, 0
            for BookData in self.CurrentBooks:
                Card = BookCard(BookData, self.ViewMode)
                Card.BookClicked.connect(self._OnBookSelected)
                
                self.GridLayout.addWidget(Card, Row, Col)
                self.BookCards.append(Card)
                
                if self.ViewMode == "list":
                    # List view: single column
                    Row += 1
                else:
                    # Grid view: multiple columns
                    Col += 1
                    if Col >= self.ColumnsCount:
                        Col = 0
                        Row += 1
            
            # Add stretch to push everything to the left
            if self.ViewMode == "list":
                self.GridLayout.setRowStretch(Row, 1)
            else:
                self.GridLayout.setColumnStretch(Col + 1, 1)
                self.GridLayout.setRowStretch(Row + 1, 1)
            
            # Process events to update display
            QApplication.processEvents()
            
            self.Logger.debug(f"Display updated with {len(self.CurrentBooks)} books in {self.ColumnsCount} columns")
            
        except Exception as Error:
            self.Logger.error(f"Failed to update display: {Error}")
    
    def _ClearGrid(self) -> None:
        """Clear all widgets from the grid"""
        try:
            # Remove all book cards
            for Card in self.BookCards:
                self.GridLayout.removeWidget(Card)
                Card.deleteLater()
            
            self.BookCards.clear()
            
        except Exception as Error:
            self.Logger.error(f"Failed to clear grid: {Error}")
    
    def _CalculateColumns(self) -> None:
        """Calculate optimal number of columns based on available width"""
        try:
            if self.ViewMode == "list":
                # List view: always single column
                self.ColumnsCount = 1
                return
                
            AvailableWidth = self.ScrollArea.viewport().width()
            
            # Account for margins and spacing
            UsableWidth = AvailableWidth - 40  # 20px margin on each side
            
            # Calculate number of columns
            ColumnsCount = max(1, UsableWidth // (self.CardWidth + 15))  # 15px spacing
            
            # Limit to reasonable range
            self.ColumnsCount = min(max(ColumnsCount, 2), 8)
            
            self.Logger.debug(f"Calculated {self.ColumnsCount} columns for width {AvailableWidth}")
            
        except Exception as Error:
            self.Logger.error(f"Failed to calculate columns: {Error}")
            self.ColumnsCount = 4  # Fallback
    
    def _OnBookSelected(self, BookData: dict) -> None:
        """Handle book selection"""
        try:
            self.BookSelected.emit(BookData)
            self.BookOpened.emit(BookData)
            self.Logger.info(f"Book selected: {BookData.get('Title', 'Unknown')}")
            
        except Exception as Error:
            self.Logger.error(f"Failed to handle book selection: {Error}")
    
    def ApplyFilters(self, Filters: dict) -> None:
        """Apply filters to the book display"""
        try:
            self.CurrentFilters = Filters.copy()
            
            if self.BookService:
                # Get filtered books from service
                Category = Filters.get('Category', '')
                Subject = Filters.get('Subject', '')
                SearchText = Filters.get('SearchText', '')
                
                if SearchText:
                    FilteredBooks = self.BookService.SearchBooks(SearchText)
                else:
                    FilteredBooks = self.BookService.GetBooksByFilters(Category, Subject)
                
                self.CurrentBooks = FilteredBooks
                self._UpdateDisplay()
                
                self.Logger.info(f"Applied filters: {len(FilteredBooks)} books match criteria")
            
        except Exception as Error:
            self.Logger.error(f"Failed to apply filters: {Error}")
    
    def HandleResize(self) -> None:
        """Handle window resize events"""
        try:
            # Recalculate columns and update display
            OldColumns = self.ColumnsCount
            self._CalculateColumns()
            
            # Only update if column count changed
            if OldColumns != self.ColumnsCount:
                self._UpdateDisplay()
                self.Logger.debug(f"Resize handled: columns changed from {OldColumns} to {self.ColumnsCount}")
            
        except Exception as Error:
            self.Logger.error(f"Failed to handle resize: {Error}")
    
    def resizeEvent(self, event):
        """Handle widget resize events"""
        super().resizeEvent(event)
        
        # Use timer to avoid too many updates during resizing
        if hasattr(self, '_ResizeTimer'):
            self._ResizeTimer.stop()
        
        self._ResizeTimer = QTimer()
        self._ResizeTimer.timeout.connect(self.HandleResize)
        self._ResizeTimer.setSingleShot(True)
        self._ResizeTimer.start(100)  # 100ms delay
    
    def GetBookCount(self) -> int:
        """Get the current number of displayed books"""
        return len(self.CurrentBooks)
    
    def SetBooks(self, Books: List[Dict]) -> None:
        """Set books to display in the grid"""
        try:
            self.CurrentBooks = Books
            self._UpdateDisplay()
            self.SelectionChanged.emit(len(Books))
            self.Logger.info(f"Set {len(Books)} books for display")
            
        except Exception as Error:
            self.Logger.error(f"Failed to set books: {Error}")
    
    def SetViewMode(self, Mode: str) -> None:
        """Set the view mode for the book grid"""
        try:
            if Mode not in ["grid", "list"]:
                self.Logger.warning(f"Unknown view mode: {Mode}")
                return
                
            if self.ViewMode != Mode:
                self.ViewMode = Mode
                
                if Mode == "grid":
                    self.CardWidth = 180
                    self.CardHeight = 280
                elif Mode == "list":
                    self.CardWidth = 600
                    self.CardHeight = 80
                
                self._UpdateDisplay()
                self.Logger.info(f"View mode set to: {Mode}")
            
        except Exception as Error:
            self.Logger.error(f"Failed to set view mode: {Error}")
    
    def RefreshDisplay(self) -> None:
        """Refresh the entire display"""
        try:
            self._LoadAllBooks()
            self.Logger.info("Book grid display refreshed")
            
        except Exception as Error:
            self.Logger.error(f"Failed to refresh display: {Error}")