# File: ColorTheme.py
# Path: Source/Utils/ColorTheme.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-05
# Last Modified: 2025-07-05  08:30PM
"""
Description: Enhanced Color Theme Module with Better Contrast
Provides professional color schemes with improved readability and contrast.
"""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import QObject


class ColorTheme(QObject):
    """
    Enhanced color theme manager for Anderson's Library with improved contrast.
    """
    
    def __init__(self):
        super().__init__()
        self.CurrentTheme = "Professional"
    
    @staticmethod
    def GetProfessionalTheme():
        """
        Professional theme with high contrast for better readability.
        """
        return {
            # Main Window Colors
            'MainBackground': '#f5f5f5',          # Light gray main background
            'WindowBorder': '#2c3e50',            # Dark blue-gray border
            
            # Left Panel Colors (High Contrast)
            'PanelBackground': '#34495e',         # Dark blue-gray background
            'PanelText': '#ffffff',               # Pure white text for maximum contrast
            'PanelTextSecondary': '#ecf0f1',      # Very light gray for secondary text
            'PanelBorder': '#2c3e50',             # Darker border
            
            # Input Field Colors  
            'InputBackground': '#ffffff',         # White input background
            'InputBorder': '#bdc3c7',             # Light gray border
            'InputText': '#2c3e50',               # Dark text
            'InputFocus': '#3498db',              # Blue focus border
            
            # Button Colors
            'ButtonBackground': '#3498db',        # Blue button background
            'ButtonText': '#ffffff',              # White button text
            'ButtonHover': '#2980b9',             # Darker blue on hover
            'ButtonPressed': '#21618c',           # Even darker when pressed
            
            # Book Card Colors
            'CardBackground': '#ffffff',          # White card background
            'CardBorder': '#e1e8ed',              # Light gray border
            'CardText': '#2c3e50',                # Dark text
            'CardHover': '#f8f9fa',               # Very light gray on hover
            'CardShadow': 'rgba(0, 0, 0, 0.1)',   # Subtle shadow
            
            # Status Bar Colors
            'StatusBackground': '#ecf0f1',        # Light gray background
            'StatusText': '#2c3e50',              # Dark text
            'StatusBorder': '#bdc3c7',            # Light border
            
            # Accent Colors
            'Primary': '#3498db',                 # Primary blue
            'Success': '#27ae60',                 # Green for success
            'Warning': '#f39c12',                 # Orange for warnings
            'Error': '#e74c3c',                   # Red for errors
            'Info': '#17a2b8',                    # Teal for info
        }
    
    @staticmethod
    def GetDarkTheme():
        """
        Dark theme with high contrast.
        """
        return {
            # Main Window Colors
            'MainBackground': '#2c3e50',
            'WindowBorder': '#34495e',
            
            # Left Panel Colors
            'PanelBackground': '#34495e',
            'PanelText': '#ecf0f1',
            'PanelTextSecondary': '#bdc3c7',
            'PanelBorder': '#2c3e50',
            
            # Input Field Colors
            'InputBackground': '#34495e',
            'InputBorder': '#7f8c8d',
            'InputText': '#ecf0f1',
            'InputFocus': '#3498db',
            
            # Button Colors
            'ButtonBackground': '#3498db',
            'ButtonText': '#ffffff',
            'ButtonHover': '#2980b9',
            'ButtonPressed': '#21618c',
            
            # Book Card Colors
            'CardBackground': '#34495e',
            'CardBorder': '#7f8c8d',
            'CardText': '#ecf0f1',
            'CardHover': '#2c3e50',
            'CardShadow': 'rgba(0, 0, 0, 0.3)',
            
            # Status Bar Colors
            'StatusBackground': '#2c3e50',
            'StatusText': '#ecf0f1',
            'StatusBorder': '#34495e',
            
            # Accent Colors
            'Primary': '#3498db',
            'Success': '#27ae60',
            'Warning': '#f39c12',
            'Error': '#e74c3c',
            'Info': '#17a2b8',
        }
    
    def GetTheme(self, ThemeName="Professional"):
        """
        Get the specified theme colors.
        
        Args:
            ThemeName: Name of the theme to retrieve
            
        Returns:
            Dictionary of color values
        """
        if ThemeName == "Professional":
            return self.GetProfessionalTheme()
        elif ThemeName == "Dark":
            return self.GetDarkTheme()
        else:
            return self.GetProfessionalTheme()  # Default to professional
    
    def GetStyleSheet(self, ThemeName="Professional"):
        """
        Generate complete Qt stylesheet for the theme.
        
        Args:
            ThemeName: Name of the theme
            
        Returns:
            Complete CSS stylesheet string
        """
        Colors = self.GetTheme(ThemeName)
        
        return f"""
        /* Main Window Styling */
        QMainWindow {{
            background-color: {Colors['MainBackground']};
            color: {Colors['PanelText']};
        }}
        
        /* Left Panel Styling with High Contrast */
        QFrame#LeftPanel {{
            background-color: {Colors['PanelBackground']};
            border: 1px solid {Colors['PanelBorder']};
            border-radius: 5px;
            padding: 10px;
        }}
        
        /* Panel Labels with High Contrast */
        QFrame#LeftPanel QLabel {{
            color: {Colors['PanelText']};
            font-weight: bold;
            font-size: 12px;
            padding: 5px 0px;
        }}
        
        /* ComboBox Styling */
        QComboBox {{
            background-color: {Colors['InputBackground']};
            border: 2px solid {Colors['InputBorder']};
            border-radius: 4px;
            padding: 8px;
            color: {Colors['InputText']};
            font-size: 11px;
            min-height: 20px;
        }}
        
        QComboBox:focus {{
            border-color: {Colors['InputFocus']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border: 2px solid {Colors['InputText']};
            width: 8px;
            height: 8px;
            border-top: none;
            border-left: none;
            transform: rotate(45deg);
            margin-right: 5px;
        }}
        
        /* LineEdit (Search Box) Styling */
        QLineEdit {{
            background-color: {Colors['InputBackground']};
            border: 2px solid {Colors['InputBorder']};
            border-radius: 4px;
            padding: 8px;
            color: {Colors['InputText']};
            font-size: 11px;
            min-height: 20px;
        }}
        
        QLineEdit:focus {{
            border-color: {Colors['InputFocus']};
        }}
        
        /* Book Card Styling */
        QFrame.BookCard {{
            background-color: {Colors['CardBackground']};
            border: 1px solid {Colors['CardBorder']};
            border-radius: 8px;
            padding: 10px;
            margin: 5px;
        }}
        
        QFrame.BookCard:hover {{
            background-color: {Colors['CardHover']};
            border-color: {Colors['Primary']};
        }}
        
        /* Book Card Labels */
        QFrame.BookCard QLabel {{
            color: {Colors['CardText']};
            font-size: 10px;
            background: transparent;
        }}
        
        /* Status Bar Styling */
        QStatusBar {{
            background-color: {Colors['StatusBackground']};
            border-top: 1px solid {Colors['StatusBorder']};
            color: {Colors['StatusText']};
            font-size: 11px;
            padding: 5px;
        }}
        
        /* Scroll Area Styling */
        QScrollArea {{
            border: none;
            background-color: {Colors['MainBackground']};
        }}
        
        QScrollBar:vertical {{
            background-color: {Colors['InputBorder']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {Colors['Primary']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {Colors['ButtonHover']};
        }}
        
        /* Button Styling */
        QPushButton {{
            background-color: {Colors['ButtonBackground']};
            color: {Colors['ButtonText']};
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 11px;
        }}
        
        QPushButton:hover {{
            background-color: {Colors['ButtonHover']};
        }}
        
        QPushButton:pressed {{
            background-color: {Colors['ButtonPressed']};
        }}
        """