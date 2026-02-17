# 👥 Team Roles & Responsibilities

## Overview

This document outlines the detailed roles, responsibilities, and weekly tasks for each team member working on the OmniAgent Morocco Gov MVP project.

**Project Duration:** 5 weeks (Week 1 → Final Week)  
**Team Size:** 2 members  
**Division Strategy:** Parallel development with strategic collaboration points

---

## 🎯 Role Definitions

### 👨‍💼 Ayoub – Data / AI / Knowledge Engineering

**Primary Responsibilities:**
- 🧠 AI & Machine Learning implementation
- 📚 Knowledge Base creation & curation
- 🔍 RAG (Retrieval-Augmented Generation) pipeline design
- 💬 Prompt engineering & optimization
- 🤖 Multi-agent system design
- 📊 AI evaluation & quality assurance
- 🖼️ OCR module integration (optional)

**Key Skills:**
- Python, AI/ML frameworks (LlamaIndex, LangChain)
- Vector databases (Chroma, FAISS)
- Prompt engineering & NLP
- RAG architecture
- Data structuring & knowledge organization

**Success Metrics:**
- Knowledge base completeness and accuracy
- RAG retrieval quality (relevance, accuracy)
- Prompt effectiveness (minimal hallucinations)
- AI evaluation scores (30+ test cases passing)

---

### 👩‍💻 Chaimae – Software / Full-Stack Engineering

**Primary Responsibilities:**
- 🔧 Backend development (FastAPI, APIs, database)
- 🎨 Frontend development (React, UI/UX)
- 🗄️ Database design & management (PostgreSQL)
- 🔐 Authentication & security
- 🐳 DevOps & deployment (Docker, Docker Compose)
- 📱 API documentation
- 🧪 Integration testing

**Key Skills:**
- Python (FastAPI, SQLAlchemy)
- JavaScript/React
- PostgreSQL & database design
- Docker & containerization
- REST API design
- Frontend styling (Tailwind CSS, CSS)

**Success Metrics:**
- All APIs fully functional & tested
- Frontend responsive & user-friendly
- Database schema optimized
- Docker setup working locally
- Zero critical bugs

---

## 📅 Weekly Breakdown

### **Week 1 – Preparation & Foundation**

#### 🧠 Ayoub's Tasks

| Task | Deliverable | Status |
|------|-------------|--------|
| 📚 Create Knowledge Base | `residence_certificate.json`, `birth_certificate.json` | ⏳ |
| 🔗 Research official sources | Compiled reference document | ⏳ |
| ❓ Write FAQ (multilingual) | 10-20 Q&A per service (Darija/Arabic/French) | ⏳ |
| 📁 Organize KB structure | `/knowledge_base/` folder hierarchy | ⏳ |
| 🧪 Prepare test questions | 30-50 evaluation questions with expected answers | ⏳ |
| 🏗️ Architecture discussion | Contribute to system design | ⏳ |

**Expected Output:**
```
/knowledge_base/
├── residence/
│   ├── residence_certificate.json
│   ├── faq.md
│   └── test_cases.json
├── birth/
│   ├── birth_certificate.json
│   ├── faq.md
│   └── test_cases.json
└── common/
    └── shared_procedures.json
```

---

#### 💻 Chaimae's Tasks

| Task | Deliverable | Status |
|------|-------------|--------|
| 🏗️ Create architecture diagram | High-level system diagram with components | ⏳ |
| 🔧 Set up GitHub repository | Organized repo with folder structure | ⏳ |
| 📋 Create project structure | `/backend`, `/frontend`, `/docs` folders | ⏳ |
| 🛠️ Setup local environment | Python + FastAPI + Node.js + React | ⏳ |
| 📝 Create initial README | Project overview & setup instructions | ⏳ |
| 🎯 Scope definition | Define 5 test scenarios with team | ⏳ |

**Expected Output:**
```
omniagent-gov-mvp/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   ├── package.json
│   └── public/
├── knowledge_base/
├── docs/
│   ├── diagrams/
│   └── architecture.md
└── README.md
```

---

#### 🤝 Joint Collaboration

- ✅ Finalize project scope document
- ✅ Agree on 5 test scenarios (document them)
- ✅ Review & approve architecture diagram
- ✅ Team kick-off meeting

---

### **Week 2 – Backend & Knowledge Finalization**

#### 🧠 Ayoub's Tasks

| Task | Deliverable | Status |
|------|-------------|--------|
| ✨ Polish Knowledge Base | Clean, consistent, multilingual KB | ⏳ |
| 🔬 Test embedding & retrieval | Local RAG prototype script | ⏳ |
| 📝 Write prompt templates | Grounding rules + multilingual support | ⏳ |
| 🧪 Test RAG locally | Verify retrieval quality | ⏳ |
| 📊 Prepare evaluation dataset | Structured test questions & answers | ⏳ |

**Expected Output:**
```python
# example_rag_prototype.py
- Test sentence embeddings
- Test vector similarity search
- Example retrieval results
- Confidence score evaluation
```

---

#### 💻 Chaimae's Tasks

| Task | Deliverable | Status |
|------|-------------|--------|
| 🗄️ Design database schema | ERD diagram + SQL migrations | ⏳ |
| 🔌 Implement core FastAPI endpoints | `/cases`, `/upload`, `/status` | ⏳ |
| 🔐 Create state machine | Case status workflow (Submitted → Approved/Rejected) | ⏳ |
| 📝 Add logging & audit trail | Track all case actions | ⏳ |
| ✅ Write API documentation | Endpoint specs & examples | ⏳ |
| 🧪 Unit test endpoints | Basic endpoint tests | ⏳ |

**Expected Endpoints:**
```
POST   /api/cases                    # Create case
POST   /api/cases/{id}/upload        # Upload document
GET    /api/cases/{id}               # Get case status
POST   /api/admin/approve/{id}       # Approve case
POST   /api/admin/reject/{id}        # Reject case
POST   /api/verify/cin               # Mock CIN check
POST   /api/verify/cnss              # Mock CNSS check
GET    /api/services                 # List services
```

---

#### 🤝 Joint Collaboration

- ✅ Review & approve database schema
- ✅ Finalize API contract (endpoints, request/response format)
- ✅ Integration checkpoint

---

### **Week 3 – Frontend + RAG Integration**

#### 🧠 Ayoub's Tasks

| Task | Deliverable | Status |
|------|-------------|--------|
| 🚀 Build RAG pipeline | LlamaIndex/LangChain implementation | ⏳ |
| 🎯 Index knowledge base | Embedded vectors in Chroma/FAISS | ⏳ |
| 💬 Integrate chat endpoint | `/api/chat/query` with RAG | ⏳ |
| 🔍 Implement retrieval logic | Query → Retrieve → Generate flow | ⏳ |
| ⚙️ Confidence checking | Fallback for low-confidence responses | ⏳ |
| 🧪 Test RAG quality | Manual & automated tests | ⏳ |

**Expected API Response:**
```json
{
  "answer": "شهادة السكنى خاصك...",
  "confidence": 0.92,
  "sources": ["residence_certificate.json"],
  "language": "darija"
}
```

---

#### 💻 Chaimae's Tasks

| Task | Deliverable | Status |
|------|-------------|--------|
| 🎨 Build React UI pages | Home, chat, upload, tracking, admin dashboard | ⏳ |
| 💬 Implement chat interface | Real-time message display, user-friendly | ⏳ |
| 📤 Add file upload component | Document upload with validation | ⏳ |
| 📊 Build case tracking page | Status display with timeline | ⏳ |
| 🔐 Implement authentication | Admin login (JWT minimal) | ⏳ |
| 🛡️ Protect admin routes | Role-based access control | ⏳ |
| 🔗 Connect frontend ↔ backend | Axios integration with error handling | ⏳ |
| 📱 Responsive design | Mobile-friendly layout | ⏳ |

**Expected Pages:**
```
/                      # Home page (service selection)
/chat/{serviceId}      # Chat interface
/upload/{caseId}       # Document upload
/cases                 # Case tracking
/admin                 # Admin dashboard (protected)
/admin/case/{id}       # Case details (admin)
```

---

#### 🤝 Joint Collaboration

- ✅ Full end-to-end test: submit → upload → track
- ✅ Test all 5 scenarios
- ✅ Integration debugging

---

### **Week 4 – OCR, Mocks, Testing & Polish**

#### 🧠 Ayoub's Tasks

| Task | Deliverable | Status |
|------|-------------|--------|
| 📸 Implement OCR module | Tesseract/EasyOCR integration (optional) | ⏳ |
| 🔍 Extract key fields | CIN, name, date extraction | ⏳ |
| ✅ Add quality checks | Image validation (blurry, missing text) | ⏳ |
| 📊 Run AI evaluation | Test 30-50 questions, measure accuracy | ⏳ |
| 📈 Optimize prompts | Reduce hallucinations, improve relevance | ⏳ |
| 📝 Document evaluation results | Report accuracy, edge cases, improvements | ⏳ |

**Expected Evaluation Metrics:**
- ✓ Accuracy: > 85%
- ✓ Hallucination rate: < 5%
- ✓ Language quality: Native speaker level
- ✓ Multilingual support: Darija/Arabic/French

---

#### 💻 Chaimae's Tasks

| Task | Deliverable | Status |
|------|-------------|--------|
| 🎭 Finalize mock APIs | Realistic CIN/CNSS responses | ⏳ |
| ❌ Add error scenarios | Invalid CIN, inactive CNSS cases | ⏳ |
| ⚠️ Improve error handling | User-friendly error messages | ⏳ |
| 📊 Admin dashboard polish | Audit log display, status filters | ⏳ |
| 🐳 Create Docker setup | Dockerfile + docker-compose.yml | ⏳ |
| 🧪 End-to-end testing | Test all 5 scenarios completely | ⏳ |
| 🎥 Record demo video | Record user workflows | ⏳ |

**Docker Deliverables:**
```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
```

---

#### 🤝 Joint Collaboration

- ✅ Comprehensive end-to-end testing (all 5 scenarios)
- ✅ Bug fixing & refinement
- ✅ Record demo video together
- ✅ Update README with screenshots

---

### **Final Week – Presentation & Wrap-up**

#### 🧠 Ayoub's Tasks

| Task | Deliverable | Status |
|------|-------------|--------|
| 📊 Prepare AI/ML presentation | Knowledge base, RAG, prompts, evaluation | ⏳ |
| 🎯 Create slides | Technical deep-dive on AI components | ⏳ |
| 💡 Demo examples | Show RAG in action, prompt examples | ⏳ |
| 📈 Include evaluation results | Charts, metrics, accuracy scores | ⏳ |
| 🧹 Code cleanup | Final comments, documentation | ⏳ |

---

#### 💻 Chaimae's Tasks

| Task | Deliverable | Status |
|------|-------------|--------|
| 🏗️ Prepare technical presentation | Architecture, backend, frontend, DevOps | ⏳ |
| 🎯 Create slides | System overview, tech stack, demo | ⏳ |
| 🎥 Live demo prep | Walkthrough of all features | ⏳ |
| 📱 Show frontend/backend interaction | API calls, data flow | ⏳ |
| 🐳 Demonstrate Docker setup | Local deployment walkthrough | ⏳ |
| 🧹 Code cleanup | Final review, formatting | ⏳ |

---

#### 🤝 Joint Collaboration

- ✅ Full presentation rehearsal
- ✅ Create final report
- ✅ Finalize README & documentation
- ✅ Clean up & commit all code
- ✅ Prepare submission package

---

## 📊 Responsibility Matrix

| Activity | Ayoub | Chaimae | Joint |
|----------|-------|---------|-------|
| Knowledge Base | 🔴 Lead | ⚪ Review | - |
| RAG Pipeline | 🔴 Lead | ⚪ Support | - |
| Backend APIs | ⚪ Review | 🔴 Lead | - |
| Frontend UI | ⚪ Test | 🔴 Lead | - |
| Database | ⚪ Review | 🔴 Lead | - |
| AI Evaluation | 🔴 Lead | ⚪ Test | - |
| Integration | ⚪ Optimize | ⚪ Optimize | 🔴 Lead |
| Testing | ⚪ AI tests | ⚪ API tests | 🔴 E2E tests |
| Documentation | 🔴 AI docs | 🔴 Tech docs | 🔴 README |
| Presentation | 🔴 AI slides | 🔴 Tech slides | 🔴 Rehearsal |

**Legend:** 🔴 = Lead | ⚪ = Support

---

## 🎯 Collaboration Points

### Critical Touchpoints

**End of Week 1:**
- ✅ Approve architecture diagram
- ✅ Finalize API contract
- ✅ Lock in knowledge base structure

**End of Week 2:**
- ✅ Database schema review
- ✅ Test API endpoints
- ✅ RAG prototype validation

**End of Week 3:**
- ✅ Full E2E integration test
- ✅ Chat integration working
- ✅ Document upload working

**End of Week 4:**
- ✅ All 5 test scenarios pass
- ✅ Demo video recorded
- ✅ No critical bugs

**Final Week:**
- ✅ Presentation rehearsal
- ✅ Final code review
- ✅ Documentation complete

---

## 📞 Communication Protocol

### Daily Standups
- **Time:** 10:00 AM (daily)
- **Duration:** 15 minutes
- **Format:** What done? What's next? Any blockers?

### Weekly Sync
- **Time:** Friday 2:00 PM (weekly)
- **Duration:** 1 hour
- **Focus:** Review progress, plan next week, resolve blockers

### Async Communication
- **Channel:** Slack/Discord for quick questions
- **Format:** GitHub issues for bugs/tasks
- **Response time:** < 4 hours

### Code Review
- **Process:** Pull request → peer review → approval → merge
- **Reviewer:** Always the other person
- **Requirement:** All PRs must pass CI/CD checks

---

## 🚀 Success Criteria

### Ayoub's Success
✅ Knowledge base: 95%+ accuracy  
✅ RAG: 85%+ relevance in top-3 results  
✅ Prompts: < 5% hallucination rate  
✅ Multilingual: Natural Darija/Arabic/French responses  
✅ AI evaluation: 30+ test cases, 85%+ pass rate  

### Chaimae's Success
✅ All APIs: 100% functional & tested  
✅ Frontend: Responsive, intuitive, zero critical bugs  
✅ Database: Optimized, consistent, audited  
✅ Docker: Single command startup  
✅ Integration: All 5 scenarios working perfectly  

### Joint Success
✅ Complete MVP delivered on time  
✅ Professional presentation given  
✅ Clean, well-documented codebase  
✅ Ready for production deployment  

---

## 📚 Resources & Tools

### Ayoub's Toolkit
```
🧠 LlamaIndex / LangChain
🎯 Sentence-Transformers
📦 Chroma / FAISS
📝 Prompt engineering patterns
🧪 Evaluation frameworks
```

### Chaimae's Toolkit
```
🔧 FastAPI / SQLAlchemy
⚛️ React / Next.js
🎨 Tailwind CSS
🐘 PostgreSQL
🐳 Docker / Docker Compose
```

### Shared Tools
```
🔀 Git / GitHub
📋 GitHub Issues / Projects
🧪 Pytest / Jest
📚 Documentation (Markdown)
```

---

## 💡 Tips for Success

### For Ayoub
- 🎯 Start with quality knowledge base — garbage in = garbage out
- 🔍 Test retrieval early & often
- 📊 Create evaluation dataset from day 1
- 💬 Get feedback from Chaimae on prompt quality
- 🧪 Be ready to iterate on prompts based on real usage

### For Chaimae
- 🗄️ Design database schema well from the start
- 🔌 API contract must be crystal clear with Ayoub
- 📱 Build UI to be flexible (easy to add features)
- 🧪 Test backend thoroughly before integrating with frontend
- 🐳 Docker setup at the end, but plan for it from the start

### For Both
- 📞 **Communicate constantly** — assumptions cause delays
- 🧪 **Test everything** — integration issues hurt timeline
- 📝 **Document as you go** — final documentation is pain
- 🎯 **Stick to the scope** — scope creep kills MVPs
- 🚀 **Ship incrementally** — demo working features regularly

---

## 🎊 Final Checklist

- [ ] Week 1: Architecture & repo setup complete
- [ ] Week 2: Backend & knowledge base finalized
- [ ] Week 3: Full integration working (chat, upload, tracking)
- [ ] Week 4: All features polished & tested
- [ ] Final week: Presentation & documentation ready
- [ ] Code is clean, documented, & ready to share
- [ ] Demo video recorded & polished
- [ ] README & all docs are comprehensive
- [ ] All code committed & pushed to GitHub
- [ ] Presentation slides are professional
- [ ] Team is confident & excited about demo! 🎉

---

## 📧 Contact & Escalation

### Ayoub – Data / AI / Knowledge Engineering
- Email: ayoub@example.com
- Primary Focus: RAG, prompts, knowledge base quality
- Escalation: If backend can't deliver chat endpoint on time

### Chaimae – Software / Full-Stack Engineering
- Email: chaimae@example.com
- Primary Focus: Backend, frontend, DevOps
- Escalation: If RAG quality is below acceptable threshold

### Project Lead (Shared)
- Decision-making authority on scope changes
- Conflict resolution for tech decisions
- Final say on deliverable quality

---

<div align="center">

## 🙌 Let's Build Something Amazing!

**Made with ❤️ in Tangier, Morocco**

Empowering citizens through AI-powered public services 🚀

Good luck to both of you! 💪

</div>
