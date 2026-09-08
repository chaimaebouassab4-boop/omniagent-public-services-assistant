# 🏗️ Dossier d'Architecture Technique du POC — OmniAgent

**Version :** 1.0  
**Environnement :** Production-ready GovTech Stack (On-Premise & Hybrid Cloud)  
**Date :** 2026  

---

## 1. Vue d'Ensemble du Système

OmniAgent repose sur une architecture moderne à 3 niveaux découplés, garantissant scalabilité, résilience et souveraineté totale des données étatiques :

`
┌─────────────────────────────────────────────────────────────────────────────┐
│                            COUCHE CITOYEN & AGENTS                          │
│  [ React + Vite Web App ]  ◄──►  [ PWA / Mobile ]  ◄──►  [ Portails Gov ]  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / JSON (JWT Authenticated)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    COUCHE API & ORCHESTRATION FASTAPI                       │
│  ┌────────────────────┐ ┌────────────────────┐ ┌─────────────────────────┐  │
│  │ Auth & Permissions │ │  Omni / Chat Router│ │ Case Management & Audit │  │
│  └─────────┬──────────┘ └──────────┬─────────┘ └────────────┬────────────┘  │
│            │                       │                        │               │
│  ┌─────────▼───────────────────────▼────────────────────────▼────────────┐  │
│  │             SYSTÈME MULTI-AGENTS SPÉCIALISÉS (LLM Engine)             │  │
│  │  • Supervisor Agent  : Routage des requêtes & détection d'intention   │  │
│  │  • Guide Agent       : Recherche RAG sur les démarches administratives │  │
│  │  • Document Agent    : Analyse OCR (CIN, Quittances, Actes PDF)       │  │
│  │  • Security Agent    : Mock CIN/CNSS & conformité CNDP                │  │
│  └─────────────────────────────────┬─────────────────────────────────────┘  │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                      COUCHE IA SOUVERAINE & DONNÉES                         │
│  ┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────┐  │
│  │  ChromaDB (Vecteurs)  │ │   Ollama LLM Local    │ │ PostgreSQL/SQLite │  │
│  │  Embeddings: bge-m3   │ │  LLaMA 3.1 / Mistral  │ │ Citoyens, Dossiers│  │
│  └───────────────────────┘ └───────────────────────┘ └───────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
`

---

## 2. Composants Détaillés

### 2.1 Interface Utilisateur (Frontend)
* **Framework :** React 18 avec Vite et TypeScript.
* **Composants UI :** Tailwind CSS + Radix UI / Lucide Icons.
* **Fonctionnalités :**
  * Support bilingue/trilingue instantané (Darija, Arabe, Français) avec bascule RTL/LTR.
  * Dialogue en streaming avec suggestions interactives de procédures.
  * Zone de dépôt sécurisée pour pièces justificatives (CIN recto/verso, contrat de bail, acte).
  * Dashboard de suivi d'avancement des dossiers pour les citoyens et espace de supervision pour les agents administratifs.

### 2.2 Backend & Orchestration (FastAPI)
* **Framework :** FastAPI (Python asynchrone).
* **Sécurité & Auth :** Tokens JWT asymétriques, validation stricte Pydantic v2, gestion granulaire des rôles (Citoyen, Agent Instructeur, Administrateur).
* **Routage :**
  * /api/omni : Hub unifié pour les requêtes citoyennes et l'orchestration conversationnelle.
  * /api/auth : Inscription, authentification sécurisée, gestion des profils et documents personnels.
  * /api/chat : Gestion de l'historique conversationnel isolé par utilisateur et injection de contexte documentaire.
  * /health : Sondes de vitalité Kubernetes/Docker (Liveness & Readiness probes).

### 2.3 Moteur RAG (Retrieval-Augmented Generation)
* **Vector Store :** ChromaDB persistant.
* **Modèle d'Embeddings :** BAAI/bge-m3 (support multilingue dense & sparse, optimisé pour l'arabe et le français).
* **Base de Connaissances Structurée :**
  * Extraction des procédures officielles marocaines issues de *service-public.ma*, *watiqa.ma*, et des textes législatifs.
  * Découpage sémantique (Chunking avec métadonnées par service, type d'acte, pièces requises, frais, délais légaux).
* **Guardrails & Anti-Hallucination :**
  * Prompting strict avec condition de refus (*Fallback*) : si la procédure n'est pas répertoriée dans la base officielle, l'agent oriente explicitement le citoyen vers le bureau d'accueil compétent au lieu d'inventer une réponse.

### 2.4 Module d'Analyse Documentaire (Document AI & OCR)
* **Moteur d'extraction :** PyPDF pour les documents natifs + EasyOCR / Tesseract pour les scans de pièces d'identité et justificatifs.
* **Extraction contextuelle :** Identification automatique du numéro de CIN, nom, prénom, adresse et date d'expiration pour pré-remplissage et vérification d'éligibilité.

---

## 3. Topologie de Déploiement & Souveraineté

| Option de Déploiement | Description | Niveau de Souveraineté | Cible Recommandée |
| :--- | :--- | :---: | :--- |
| **Option A : On-Premise Air-Gapped** | Déploiement 100% interne sur serveurs physiques de l'administration (GPU NVIDIA). Aucun accès Internet requis. | 🔒 Maximale (100%) | Ministère de l'Intérieur, Défense, Justice |
| **Option B : Cloud Souverain National** | Hébergement sur Datacenter marocain certifié CNDP/DGSSI (Maroc Telecom Cloud, Inwi Cloud, N+ONE). | 🔒 Haute (100% Maroc) | Agences Nationales, Régions, Communes |
| **Option C : Hybride Accéléré** | Base documentaire locale + inférence sécurisée par passerelle souveraine de l'État. | 🔒 Haute | Pilotes et démonstrations inter-administrations |
