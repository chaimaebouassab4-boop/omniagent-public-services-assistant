# omniagent-public-services-assistant
An AI-powered citizen service agent for Moroccan public administration

## 📖 About

OmniAgent Morocco Gov MVP is a proof-of-concept GovTech AI project that demonstrates how Generative AI and RAG (Retrieval-Augmented Generation) can bridge the gap between citizens and public administration in Morocco.

The system acts as an intelligent administrative assistant, helping citizens:

- Understand administrative procedures in simple language (Darija / Arabic / French)
- Get step-by-step guidance on required documents, fees, and processing times
- Submit service requests and track their status
- Receive automated validation and guidance


## 👥 Team & Roles

### Ayoub - Data / AI / Knowledge Engineering
- Collected and structured the Knowledge Base (procedures, FAQs, requirements)
- Designed and implemented the RAG pipeline
- Prompt engineering with strict grounding rules (Darija/Arabic/French)
- AI answer evaluation and testing
- OCR module integration

### Chaimae - Software / Full-Stack Engineering
- Backend development (FastAPI, PostgreSQL, REST APIs)
- Frontend development (React chat UI, upload, tracking, admin dashboard)
- Mock API integration (CIN/CNSS verification)
- Workflow state machine implementation
- Docker setup and deployment configuration
---

## ✨ Features

### For Citizens

- **💬 Conversational Chat Interface** - Ask questions naturally in Darija, Arabic, or French
- **📋 Procedure Guidance** - Step-by-step instructions for administrative services
- **📄 Document Upload** - Submit required documents with basic validation
- **🔍 Request Tracking** - Monitor the status of submitted requests
- **✅ Automated Validation** - Instant feedback on document completeness

### For Administrators

- **📊 Admin Dashboard** - Review and manage citizen requests
- **🔐 Mock Verification** - Simulated CIN and CNSS validation
- **📝 Case Management** - Update request status and add notes

### Technical Features

- **🤖 Multi-Agent Architecture** - Specialized agents for intake, guidance, documents, and workflow
- **🧠 RAG Pipeline** - Grounded responses from curated knowledge base
- **🔒 Prompt Engineering** - Strict rules to prevent hallucinations
- **📸 OCR Support** - Extract text from uploaded documents (optional)
- **🐳 Dockerized** - Easy local deployment

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database for structured data
- **LlamaIndex / LangChain** - RAG orchestration
- **Chroma / FAISS** - Vector database for knowledge retrieval

### Frontend
- **React.js / Next.js** - Interactive user interface
- **Tailwind CSS** - Modern styling
- **Axios** - API communication

### AI/ML
- **Ollama / Grok / OpenAI** - Large Language Model
- **Tesseract / EasyOCR** - Optical character recognition (optional)
- **Prompt Engineering** - Custom guardrails and grounding rules

### DevOps
- **Docker & Docker Compose** - Containerization
- **Git** - Version control

---

## 🏗️ Architecture

### Multi-Agent System

The system employs a coordinated multi-agent architecture where specialized agents handle different aspects of citizen interaction:

- **Supervisor Agent** - Orchestrates agent coordination and workflow
- **Intake Agent** - Detects user intent and identifies requested service
- **Guide Agent** - Answers questions using RAG-powered knowledge retrieval
- **Document Agent** - Validates uploaded documents using OCR
- **Workflow Agent** - Manages request lifecycle and status transitions
- **Security Agent** - Performs mock identity and CNSS verification

### System Overview

```
[Citizen] → [Chat Interface] → [Intake Agent] → [Guide/Document/Workflow Agents]
                                     ↓
                         [Knowledge Base + RAG]
                                     ↓
                         [Vector Database]
```

Detailed diagrams (class, sequence, architecture) are available in `/docs/diagrams/`

---

### Example Queries

**In Darija:**
```
- "شنو خاصني باش ندير شهادة السكنى؟" 
  (What do I need for a residence certificate?)
- "شحال كيخلص؟" 
  (How much does it cost?)
- "فين نمشي نديرها؟" 
  (Where do I go to get it?)
```

**In French:**
```
- "Quels sont les documents nécessaires pour un certificat de résidence ?"
- "Combien de temps faut-il pour obtenir l'extrait de naissance ?"
```

**In Arabic:**
```
- "ما هي الوثائق المطلوبة لشهادة الإقامة؟"
```

### Testing the Workflow

1. **Ask a question** via the chat interface
2. **Submit a request** by selecting a service and uploading documents
3. **Track status** in the "My Requests" section
4. **Admin review** via the admin dashboard (login as admin)

### API Endpoints

- `POST /api/chat` - Send chat message
- `POST /api/requests` - Create new service request
- `GET /api/requests/{id}` - Get request status
- `POST /api/documents/upload` - Upload document
- `GET /api/kb/services` - List available services

Full API documentation: http://localhost:8000/docs

---


### Shared Contributions
- System architecture and agent design
- UML diagrams (class, sequence, use case)
- Testing scenarios and demo preparation
- Documentation and final presentation

---

## 🗺️ Roadmap & Future Improvements

### Current MVP Limitations

- Only 2 services supported
- No real government API integration
- Mocked identity verification
- Local deployment only
- Limited document validation

### Planned Enhancements

- [ ] Add 10+ additional administrative services
- [ ] Integration with real government APIs (when available)
- [ ] Advanced OCR with document type classification
- [ ] Multi-language UI (full Darija support)
- [ ] Mobile application (iOS/Android)
- [ ] SMS/WhatsApp notification integration
- [ ] Advanced analytics dashboard
- [ ] Cloud deployment (Azure/AWS)
- [ ] Accessibility improvements (screen readers, WCAG compliance)
- [ ] Performance optimization for scale

---

## 📂 Project Structure

```
omniagent-gov-mvp/
├── docs/                    # Documentation & diagrams
├── knowledge_base/          # Curated KB, FAQ, evaluation
├── backend/                 # FastAPI application
├── frontend/                # React application
├── docker-compose.yml       # Container orchestration
└── README.md               # This file
```

## 🙏 Acknowledgments

- Moroccan citizens who inspired this project
- Open-source AI/ML community
- GovTech innovators worldwide



<div align="center">

Made with ❤️ in Tangier, Morocco

Empowering citizens through AI-powered public services

</div>
