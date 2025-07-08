# File: README_AndyWeb.md
# Path: README_AndyWeb.md
# Standard: AIDEV-PascalCase-1.8
# Created: 2025-07-07
# Last Modified: 2025-07-07  04:35PM
---

# 🚀 AndyWeb - Anderson's Library Web Edition

**Modern web interface for your book library with FastAPI backend and responsive frontend.**

## 🔥 Quick Start (Zero Config!)

1. **Just run the launcher:**
   ```bash
   python StartAndyWeb.py
   ```

2. **That's it!** The launcher will:
   - ✅ Check Python version (3.8+)
   - ✅ Verify database exists
   - ✅ Install missing dependencies
   - ✅ Start FastAPI server
   - ✅ Open browser automatically

3. **Access your library:**
   - **Main App:** http://127.0.0.1:8000/app
   - **API Docs:** http://127.0.0.1:8000/api/docs
   - **API Root:** http://127.0.0.1:8000/api

---

## 📱 What You Get

### **Beautiful Web Interface**
- 📚 **Grid view** with book thumbnails
- 🔍 **Real-time search** across titles, authors, topics
- 🏷️ **Smart filtering** by category and subject
- 📊 **Library statistics** dashboard
- 📱 **Mobile responsive** design

### **Powerful API Backend**
- ⚡ **FastAPI** with automatic documentation
- 🗃️ **SQLite database** (your existing MyLibraryWeb.db)
- 🚀 **Fast JSON responses** with thumbnail support
- 📄 **Pagination** for large libraries
- 🔒 **Ready for authentication** (Google auth coming)

### **Developer Friendly**
- 🔄 **Auto-reload** during development
- 📚 **Interactive API docs** at `/api/docs`
- 🧪 **Built-in testing** endpoints
- 🏗️ **Modular architecture** following Design Standard v1.8

---

## 🛠️ Architecture Overview

```
AndyWeb/
├── Source/
│   ├── API/
│   │   └── MainAPI.py          # FastAPI application
│   └── Core/
│       └── DatabaseManager.py  # Database operations
├── WebPages/
│   └── index.html              # Frontend interface
├── Data/Databases/
│   └── MyLibraryWeb.db        # Your book database
└── StartAndyWeb.py            # One-click launcher
```

---

## 🎯 Current Features

### **✅ MVP Complete**
- [x] **Browse books** with thumbnails and metadata
- [x] **Search functionality** across all fields
- [x] **Category/subject filtering** 
- [x] **Pagination** for performance
- [x] **Database statistics**
- [x] **Responsive design** for mobile/tablet
- [x] **Auto-setup** and dependency management

### **🚧 Coming Next**
- [ ] **Book details modal** with full metadata
- [ ] **PDF viewer integration** for local files
- [ ] **Google Drive integration** for cloud storage
- [ ] **User authentication** with Google
- [ ] **Reading progress tracking**
- [ ] **User notes and ratings**

### **🔮 Future Vision**
- [ ] **Multi-user support**
- [ ] **MySQL backend** for production
- [ ] **Mobile app** using same API
- [ ] **Recommendation engine**
- [ ] **Social features** and sharing

---

## 🚀 Development Stack

| Component | Technology | Why? |
|-----------|------------|------|
| **Backend** | FastAPI | Modern, fast, automatic docs |
| **Database** | SQLite → MySQL | Start simple, scale later |
| **Frontend** | Vanilla JS | No build process, progressive |
| **Styling** | CSS3 | Modern responsive design |
| **Auth** | Google OAuth | Future integration ready |
| **Hosting** | Free tier | $0 budget constraint |

---

## 🔧 Troubleshooting

### **Database Issues**
```bash
# Check if database exists
python StartAndyWeb.py --check

# If missing, check path:
Data/Databases/MyLibraryWeb.db
```

### **Dependency Issues**
```bash
# Manual install
pip install -r requirements.txt

# Or use launcher auto-install
python StartAndyWeb.py
```

### **Port Conflicts**
If port 8000 is busy, the server will show an error. Kill other processes or change port in `MainAPI.py`.

### **Python Version**
Requires Python 3.8+. Check with:
```bash
python --version
```

---

## 📚 API Reference

### **Books Endpoints**
- `GET /api/books` - List books with pagination/filtering
- `GET /api/books/{id}` - Get book details
- `GET /api/books/{id}/thumbnail` - Get book thumbnail image
- `GET /api/books/{id}/file` - Stream book file (if local)

### **Library Endpoints**
- `GET /api/categories` - List all categories with counts
- `GET /api/subjects` - List subjects (optionally by category)
- `GET /api/stats` - Database statistics and recent activity

### **System Endpoints**
- `GET /api/health` - Health check for monitoring
- `GET /api/docs` - Interactive API documentation

---

## 🎯 Design Philosophy

**Built following Project Himalaya Design Standard v1.8:**
- ✅ **PascalCase naming** throughout
- ✅ **Comprehensive headers** in every file
- ✅ **Modular architecture** for maintainability
- ✅ **Zero SQLAlchemy** dependency per requirements
- ✅ **Free services only** for hosting
- ✅ **Progressive enhancement** approach

---

## 🤝 Contributing

This is part of **Project Himalaya** - Herb's personal library system. 

**Key principles:**
- Follow Design Standard v1.8 religiously
- Use actual timestamps in headers
- Keep modules under 300 lines
- Test thoroughly before committing
- Document everything clearly

---

## 🏔️ Go Himalaya!

**From desktop Qt to modern web in one clean migration. Zero legacy baggage, maximum future potential!**

*Ready to build the next phase? Let's add Google Drive integration!* 🚀