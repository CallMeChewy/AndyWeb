# Replace the subjects endpoint in your MainAPI.py with this fixed version:

@App.get("/api/subjects", response_model=List[SubjectResponse])
async def GetSubjects(category: Optional[str] = Query(default=None, description="Filter by category name")):
    """
    Get all subjects with book counts
    Optionally filtered by category NAME (not ID)
    FIXED: sqlite3.Row access and proper category filtering
    """
    try:
        DatabaseManager = GetDatabase()
        
        if not DatabaseManager.Connect():
            raise HTTPException(status_code=503, detail="Database connection failed")
        
        # FIXED: Use category name for filtering, not category_id
        if category:
            SubjectsData = DatabaseManager.GetSubjectsByCategory(category)
        else:
            SubjectsData = DatabaseManager.GetSubjectsWithCounts()
        
        # FIXED: Remove .get() method and handle missing columns properly
        Subjects = []
        for Row in SubjectsData:
            try:
                # Handle both possible column names and missing columns
                subject_name = Row['Subject'] if 'Subject' in Row.keys() else Row.get('subject', '')
                category_name = Row['Category'] if 'Category' in Row.keys() else Row.get('category', '')
                book_count = Row['BookCount'] if 'BookCount' in Row.keys() else Row.get('count', 0)
                
                if subject_name:  # Only add if subject name exists
                    Subjects.append(SubjectResponse(
                        name=subject_name,
                        category=category_name,
                        count=book_count
                    ))
            except Exception as RowError:
                Logger.warning(f"Skipping row due to error: {RowError}")
                continue
        
        Logger.info(f"✅ Retrieved {len(Subjects)} subjects for category: {category or 'All'}")
        return Subjects
        
    except Exception as Error:
        Logger.error(f"Error getting subjects: {Error}")
        Logger.error(f"Error type: {type(Error)}")
        Logger.error(f"Category parameter: {category}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve subjects: {str(Error)}")