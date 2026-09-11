# 🔐 Dossier Juridique — Propriété Intellectuelle & Licences Logicielles

**Objet :** Cadre des droits d'auteur, licences des composants open-source et transfert des droits d'usage  
**Cadre Légal :** Loi marocaine n° 2-00 relative aux droits d'auteur et droits voisins, Code de la propriété industrielle  
**Solution :** OmniAgent Public Services Assistant  

---

## 1. Titularité du Code Source & Développements Spécifiques

* **Développements Propriétaires / Spécifiques :**
  L'ensemble du code applicatif développé pour le projet (orchestration FastAPI, modules de routage conversationnel, prompts d'ancrage réglementaire, composants UI React/Tailwind, scripts de tests et de benchmark) constitue une œuvre de l'esprit originale protégée par le droit d'auteur.
* **Garantie d'Éviction :**
  Le titulaire garantit à l'acheteur public que la solution est exempte de toute contrefaçon et qu'aucun brevet, droit d'auteur ou droit de tiers n'est violé par son utilisation.
* **Modalité de Cession pour la Commande Publique :**
  Conformément aux clauses des CCAG-EMO / CCAG-Prestations Intellectuelles des marchés publics marocains, l'acheteur public bénéficie d'une **licence d'exploitation exclusive, pérenne et sans limitation de durée** pour ses propres besoins institutionnels, avec accès au code source pour audit et maintenance souveraine.

---

## 2. Inventaire des Composants Open Source & Licences Compatibles

Tous les composants tiers intégrés respectent des licences hautement permissives autorisant l'usage commercial et l'intégration dans les systèmes gouvernementaux sans contamination de type copyleft viral :

| Composant | Rôle Technique | Licence | Compatibilité Marché Public |
| :--- | :--- | :--- | :---: |
| **FastAPI** | Framework API Web Asynchrone | MIT License | ✅ 100% Compatible |
| **Uvicorn / Starlette** | Serveur ASGI & Middleware | BSD 3-Clause | ✅ 100% Compatible |
| **React / Next.js** | Interface Utilisateur Citoyenne | MIT License | ✅ 100% Compatible |
| **Tailwind CSS** | Moteur de styles & Responsive UI | MIT License | ✅ 100% Compatible |
| **ChromaDB** | Base vectorielle d'embeddings | Apache 2.0 | ✅ 100% Compatible |
| **PyPDF** | Extraction de contenu de documents | BSD 3-Clause | ✅ 100% Compatible |
| **Pydantic v2** | Typage et validation de données | MIT License | ✅ 100% Compatible |
| **Ollama / LLaMA 3.1** | Moteur d'inférence LLM local | LLaMA 3.1 Community License / Apache 2.0 | ✅ Conforme usage public |

---

## 3. Absence de Dépendance Propriétaire Externe (*No Vendor Lock-in*)

* La solution ne dépend d'aucun service cloud propriétaire fermé (aucun abonnement obligatoire à une API propriétaire étrangère).
* Les modèles LLM peuvent être librement substitués (ex: passer de LLaMA à Mistral ou à un modèle national souverain entraîné par les universités marocaines) sans réécrire l'architecture applicative.
