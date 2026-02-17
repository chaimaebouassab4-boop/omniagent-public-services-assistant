# 🚀 Quick Setup Guide - PowerShell Script (CORRECTED VERSION)

## ✅ What Changed?

The corrected version (`setup-project-CORRECTED.ps1`) now uses proper **here-string syntax** with:
- ✓ Single-quoted here-strings (`@' ... '@`)
- ✓ Proper UTF-8 encoding handling
- ✓ No garbled characters for Darija/Arabic text
- ✓ All multi-line content properly formatted

---

## 📥 Download & Setup

### Step 1: Download the File
Download `setup-project-CORRECTED.ps1` from the outputs folder

### Step 2: Save with UTF-8 Encoding (IMPORTANT!)

If you edit it in **VS Code**:
1. Open the file
2. Look at bottom-right corner → see encoding indicator
3. Click it → Select **"Save with Encoding"**
4. Choose **UTF-8** (or UTF-8 with BOM)
5. Save the file (Ctrl+S)

---

## 🎯 Run the Script

### Option 1: Simple Bypass (Recommended)
```powershell
powershell -ExecutionPolicy Bypass -File .\setup-project-CORRECTED.ps1
```

### Option 2: Set Execution Policy for Session Only
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\setup-project-CORRECTED.ps1
```

### Option 3: From Command Prompt (cmd.exe)
```cmd
powershell -ExecutionPolicy Bypass -File ".\setup-project-CORRECTED.ps1"
```

---

## ✨ What Gets Created

The script will automatically create:

```
✅ 40+ Folders
✅ 80+ Files
✅ All configurations (Docker, frontend, backend)
✅ Knowledge base templates
✅ Documentation structure
```

**Total output:** ~150+ files and folders ready to go!

---

## 📋 Expected Output

When you run it, you'll see:

```
🚀 OmniAgent Morocco Gov MVP - Project Setup
============================================================

📁 Creating main project directories...
------------------------------------------------------------
✅ Created folder: docs
✅ Created folder: docs/diagrams
✅ Created folder: docs/api
✅ Created folder: knowledge_base
... (many more) ...

🔧 Creating backend files...
------------------------------------------------------------
✅ Created file: backend/requirements.txt
✅ Created file: backend/app/main.py
... (many more) ...

🎨 Creating frontend files...
------------------------------------------------------------
✅ Created file: frontend/package.json
✅ Created file: frontend/vite.config.js
... (many more) ...

📚 Creating knowledge base files...
------------------------------------------------------------
✅ Created file: knowledge_base/residence/residence_certificate.json
✅ Created file: knowledge_base/birth/birth_certificate.json
... (more files) ...

🐳 Creating Docker files...
------------------------------------------------------------
✅ Created file: backend/Dockerfile
✅ Created file: docker-compose.yml
... (more files) ...

📖 Creating documentation files...
------------------------------------------------------------
✅ Created file: docs/diagrams/ARCHITECTURE.md
... (more files) ...

📄 Creating project root files...
------------------------------------------------------------
✅ Created file: .gitignore
✅ Created file: STRUCTURE.md

============================================================
✅ Project Structure Created Successfully!
============================================================

📊 Summary:
  ✓ Backend structure (FastAPI + agents + models)
  ✓ Frontend structure (React + components)
  ✓ Knowledge base templates
  ✓ Docker configuration
  ✓ Documentation templates

🚀 Next Steps:

1. Initialize Git repository:
   git init
   git add .
   git commit -m 'Initial project structure'

2. Setup backend:
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt

3. Setup frontend:
   cd frontend
   npm install

4. Start development:
   docker-compose up -d
   OR run backend and frontend separately

📁 Project is ready at: C:\Users\YOGA\Music\omni\omniagent-public-services-assistant

Happy coding! 💪
```

---

## ⚡ Quick Commands After Setup

### Initialize Git
```bash
git init
git add .
git commit -m "Initial project structure"
```

### Setup Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Setup Frontend
```bash
cd frontend
npm install
```

### Run with Docker
```bash
docker-compose up -d
```

---

## 🔧 Troubleshooting

### Issue: Still getting execution policy error?
**Solution:** Use the full command:
```powershell
powershell -ExecutionPolicy Bypass -File "C:\full\path\to\setup-project-CORRECTED.ps1"
```

### Issue: Encoding error (garbled text)?
**Solution:** 
1. Open file in VS Code
2. Save as UTF-8 (bottom-right corner)
3. Run again

### Issue: "command not found" or "script not found"?
**Solution:** Make sure you're in the right directory:
```powershell
# First navigate to your project folder
cd C:\Users\YOGA\Music\omni\omniagent-public-services-assistant

# Then run
powershell -ExecutionPolicy Bypass -File .\setup-project-CORRECTED.ps1
```

---

## 📞 Need Help?

If something goes wrong:

1. **Check if you're in the right folder:**
   ```powershell
   ls *.ps1
   ```
   Should show `setup-project-CORRECTED.ps1`

2. **Verify the file was saved as UTF-8:**
   - Right-click file → Properties
   - Open with Notepad to check for encoding issues

3. **Run with detailed output:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\setup-project-CORRECTED.ps1 -Verbose
   ```

4. **Try the batch file alternative instead:**
   - Use `setup-project.bat` if PowerShell keeps giving issues

---

## ✅ Success Checklist

After running the script, you should have:

- [ ] All folders created (docs, backend, frontend, knowledge_base)
- [ ] Backend files in place (requirements.txt, main.py, agents, models, routes)
- [ ] Frontend files in place (package.json, React components, pages)
- [ ] Knowledge base files (residence, birth certificates)
- [ ] Docker files (docker-compose.yml, Dockerfiles)
- [ ] Documentation templates
- [ ] .gitignore file
- [ ] STRUCTURE.md file

If all checkboxes are ticked ✓, you're ready to start coding! 🎉

---

## 🎊 Next Phase: Development

Once the structure is created:

1. **For Ayoub (AI/Data):**
   - Start building the Knowledge Base
   - Design RAG pipeline
   - Write prompt templates

2. **For Chaimae (Full-Stack):**
   - Setup database schema
   - Implement FastAPI endpoints
   - Build React components

3. **Together:**
   - Review architecture
   - Plan integration points
   - Setup version control

---

## 📧 Questions?

Good luck with your project! 🚀 You're all set to start building the OmniAgent Morocco Gov MVP!

Made with ❤️ in Tangier, Morocco
