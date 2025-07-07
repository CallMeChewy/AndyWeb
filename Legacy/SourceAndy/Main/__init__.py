# Create these __init__.py files in the appropriate directories:

# File: __init__.py
# Path: Source/__init__.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-04
# Last Modified: 2025-07-04  04:12PM
"""
Description: Anderson's Library Source Package
Root package for all Anderson's Library source code modules.
"""

__version__ = "1.0.0"
__author__ = "Herb Bowers"
__project__ = "Project Himalaya"


# File: __init__.py
# Path: Source/Data/__init__.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-04
# Last Modified: 2025-07-04  04:12PM
"""
Description: Data Layer Package
Contains data models, database schemas, and data access objects.
"""

from .DatabaseModels import (
    BookRecord, SearchCriteria, SearchResult, CategoryInfo, 
    LibraryStatistics, CreateBookRecordFromDict, ValidateBookRecord
)

__all__ = [
    'BookRecord', 'SearchCriteria', 'SearchResult', 'CategoryInfo',
    'LibraryStatistics', 'CreateBookRecordFromDict', 'ValidateBookRecord'
]


# File: __init__.py
# Path: Source/Core/__init__.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-04
# Last Modified: 2025-07-04  04:12PM
"""
Description: Core Services Package
Contains business logic, database managers, and core application services.
"""

from .DatabaseManager import DatabaseManager
from .BookService import BookService

__all__ = ['DatabaseManager', 'BookService']


# File: __init__.py
# Path: Source/Interface/__init__.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-04
# Last Modified: 2025-07-04  04:12PM
"""
Description: User Interface Package
Contains all GUI components, windows, dialogs, and interface elements.
"""

from .FilterPanel import FilterPanel
from .BookGrid import BookGrid, BookTile
from .MainWindow import AndersonMainWindow, RunApplication

__all__ = ['FilterPanel', 'BookGrid', 'BookTile', 'AndersonMainWindow', 'RunApplication']


# File: __init__.py
# Path: Source/Utils/__init__.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-04
# Last Modified: 2025-07-04  04:12PM
"""
Description: Utilities Package
Contains utility functions, helpers, and shared components.
"""

# This package will contain utility modules as they are created
__all__ = []


# File: __init__.py
# Path: Source/Framework/__init__.py
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-04
# Last Modified: 2025-07-04  04:12PM
"""
Description: Framework Package
Contains framework components like CustomWindow and shared UI elements.
"""

# Will contain CustomWindow and other framework components
# from .CustomWindow import CustomWindow
# __all__ = ['CustomWindow']
__all__ = []