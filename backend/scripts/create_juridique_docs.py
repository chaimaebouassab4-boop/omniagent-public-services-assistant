import os

base_dir = r'c:\Users\21263\OneDrive\Desktop\omnia.agent\omniagent-public-services-assistant'
juridique_dir = os.path.join(base_dir, 'docs', 'dossier_juridique')
os.makedirs(juridique_dir, exist_ok=True)

# 1. CNDP / LOI 09-08
doc1 = '''# ⚖️ Dossier Juridique — Conformité CNDP & Loi 09-08

**Objet :** Protection des personnes physiques à l'égard du traitement des données à caractère personnel  
**Cadre Légal :** Loi marocaine n° 09-08 promulguée par le Dahir n° 1-09-15 et décrets d'application  
**Autorité de Tutelle :** Commission Nationale de contrôle de la protection des Données à caractère Personnel (CNDP)  
**Solution :** OmniAgent Public Services Assistant  

---

## 1. Déclaration Préalable & Engagement de Conformité

La plateforme **OmniAgent** a été conçue selon le principe du **Privacy by Design & by Default**. Dans le cadre d'un déploiement auprès d'une entité publique marocaine, le système fait l'objet d'une déclaration préalable ou d'une demande d'autorisation auprès de la **CNDP** conformément aux articles 12 et suivants de la Loi 09-08.

---

## 2. Cartographie des Données Traitées

| Type de Donnée | Catégorie | Base Légale | Durée de Conservation | Mesure de Protection |
| :--- | :--- | :--- | :--- | :--- |
| **Identité Civile** (Nom, Prénom, CIN) | Données à caractère personnel | Mission d'intérêt public / Démarche administrative | Durée de traitement de la demande + 30 jours | Chiffrement en base (AES-256), hachage sécurisé |
| **Coordonnées** (Téléphone, Email) | Données de contact | Consentement de l'usager | Durée du compte citoyen | Restriction d'accès par rôle (RBAC) |
| **Documents justificatifs** (CIN, Contrats, Factures) | Fichiers numériques / Scans | Traitement du dossier administratif | Archivage temporaire sécurisé | Stockage cloisonné, pas d'exposition de chemin direct |
| **Logs de requêtes sémantiques** | Questions posées à l'IA | Amélioration du service public | 90 jours (pseudonymisées) | Dé-identification automatique de toute donnée nominative |

---

## 3. Droits des Citoyens Garantis (Articles 7 à 9)

* **Droit d'Information :** Lors de l'inscription et de la première interaction, une mention explicite informe le citoyen de la finalité du traitement, du responsable de traitement et de ses droits légaux.
* **Droit d'Accès & de Rectification :** Le citoyen accède directement à son profil via l'API /api/auth/me et peut actualiser ses données personnelles (téléphone, nom).
* **Droit à l'Oubli / Suppression :** L'usager dispose d'une fonctionnalité directe de purge de son historique de conversation (DELETE /api/chat/messages) et peut demander la clôture de son dossier.

---

## 4. Mesures Techniques et Organisationnelles de Sécurité (Article 23)

1. **Isolation stricte des sessions :** Chaque citoyen ne peut accéder qu'aux données rattachées à son propre identifiant chiffré par token JWT.
2. **Cloisonnement des répertoires de fichiers :** Les fichiers uploadés sont stockés dans des répertoires dédiés et protégés contre toute lecture directe sans authentification d'administrateur ou du propriétaire.
3. **Audit Trail & Journalisation :** Chaque action (consultation, téléchargement de pièce, modification de statut) fait l'objet d'une ligne d'audit horodatée inaltérable.
'''

with open(os.path.join(juridique_dir, '01_CONFORMITE_CNDP_LOI_09_08.md'), 'w', encoding='utf-8') as f:
    f.write(doc1)

# 2. LOI 55-19
doc2 = '''# 📜 Dossier Juridique — Conformité Loi 55-19 sur la Simplification Administrative

**Objet :** Simplification des procédures et des formalités administratives  
**Cadre Légal :** Loi marocaine n° 55-19 promulguée par le Dahir n° 1-20-06 du 6 mars 2020  
**Portée :** Administrations de l'État, établissements et entreprises publics, collectivités territoriales  
**Rôle d'OmniAgent :** Outil technologique garant du respect strict des principes de la Loi 55-19  

---

## 1. Alignement avec les Principes Directeurs de la Loi 55-19

La Loi 55-19 a fixé des obligations impératives pour moderniser la relation usager-administration. OmniAgent intègre nativement ces contraintes dans sa logique métier :

### 1.1 Principe de Non-Redondance Documentaire (Article 9)
> *\"Il est interdit à l'administration d'exiger de l'usager la fourniture de documents ou d'informations dont elle dispose déjà ou qui peuvent être obtenus auprès d'autres administrations.\"*
* **Implémentation OmniAgent :** L'agent IA n'oriente jamais le citoyen vers la production de copies certifiées non conformes ou de documents redondants. Il précise les pièces strictement autorisées par le répertoire national unifié des décisions administratives.

### 1.2 Interdiction de Demander Plus d'un Exemplaire (Article 10)
> *\"L'administration ne peut en aucun cas exiger de l'usager la production de plus d'un seul exemplaire du dossier de demande ou des documents le composant.\"*
* **Implémentation OmniAgent :** Le dépôt numérique s'effectue en exemplaire unique dématérialisé (PDF/PNG), éliminant les copies papier superflues.

### 1.3 Suppression de la Légalisation de Signature pour les Décisions Numériques (Article 11)
> *\"Suppression de la légalisation de signature pour les documents et actes établis sous forme électronique lorsqu'ils sont certifiés conformes selon les lois en vigueur.\"*
* **Implémentation OmniAgent :** L'assistant sensibilise l'usager sur les démarches où le déplacement physique pour légalisation n'est plus requis, orientant directement vers l'authentification électronique sécurisée.

### 1.4 Transparence des Délais et Droits de Réponse (Articles 13 & 14)
* **Obligation légale :** Fixation d'un délai maximal de réponse de l'administration (ne pouvant excéder 60 jours, ramené à 30 jours pour les actes courants).
* **Implémentation OmniAgent :** Chaque fiche procédure affichée par l'agent indique explicitement le délai légal d'instruction officiel et informe le citoyen du principe *\"le silence vaut accord\"* lorsque prévu par la loi.

---

## 2. Matrice d'Évaluation de la Conformité

| Article Loi 55-19 | Exigence Légale | Fonctionnalité OmniAgent | Statut |
| :--- | :--- | :--- | :---: |
| **Art. 8** | Répertoire officiel des décisions | Ancrage RAG strict sur le corpus officiel sans hallucination | ✅ Conforme |
| **Art. 9** | Suppression des justificatifs redondants | Validation des dossiers sur la liste officielle minimale | ✅ Conforme |
| **Art. 13** | Information sur les délais légaux | Notification automatique des délais légaux de traitement | ✅ Conforme |
| **Art. 18** | Numérisation des formalités | Dépôt dématérialisé et suivi d'état d'avancement en ligne | ✅ Conforme |
'''

with open(os.path.join(juridique_dir, '02_CONFORMITE_LOI_55_19.md'), 'w', encoding='utf-8') as f:
    f.write(doc2)

# 3. PROPRIETE INTELLECTUELLE & LICENCES
doc3 = '''# 🔐 Dossier Juridique — Propriété Intellectuelle & Licences Logicielles

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
'''

with open(os.path.join(juridique_dir, '03_PROPRIETE_INTELLECTUELLE_ET_LICENCES.md'), 'w', encoding='utf-8') as f:
    f.write(doc3)

# 4. DGSSI / SECURITE SOUVERAINETE
doc4 = '''# 🛡️ Dossier Juridique & Technique — Sécurité et Souveraineté Numérique DGSSI

**Objet :** Conformité aux exigences de sécurité des systèmes d'information et souveraineté des données étatiques  
**Cadre Réglementaire :** 
- Décret n° 2-15-712 fixant les règles de sécurité des systèmes d'information
- Directive Nationale de Sécurité des Systèmes d'Information (DNSSI) émise par la **DGSSI** (Direction Générale de la Sécurité des Systèmes d'Information)
- Loi n° 05-20 relative à la cybersécurité  

---

## 1. Principe Fondamental : Zéro Fuite de Données Citoyennes Hors du Territoire

Contrairement aux solutions basées sur des API d'IA générative étrangères (OpenAI, Anthropic, Google Cloud public), **OmniAgent a été conçu pour un fonctionnement souverain étanche** :

1. **Inférence Locale On-Premise :** Le modèle de langage (LLM) s'exécute directement sur les serveurs de l'administration ou sur un cloud souverain hébergé physiquement au Maroc (Datacenter certifié DGSSI/CNDP).
2. **Pas d'Envoi Extérieur :** Aucune question de citoyen, aucun numéro de CIN, aucun extrait d'acte civil ne transite sur l'Internet public ni vers des serveurs situés hors des frontières du Royaume.
3. **Index Vectoriel Isolé :** La base de connaissances ChromaDB est stockée localement sur le disque sécurisé du serveur avec chiffrement au repos.

---

## 2. Matrice d'Exigences DNSSI / DGSSI

| Domaine DNSSI | Règle de Sécurité | Mesure Implémentée dans OmniAgent |
| :--- | :--- | :--- |
| **Contrôle d'Accès** | Règle d'authentification forte et principe du moindre privilège | Authentification JWT, expiration paramétrable, séparation stricte rôles usagers et rôles instructeurs. |
| **Chiffrement** | Chiffrement des flux et des données stockées sensibles | Flux HTTPS/TLS 1.3 obligatoire, chiffrement AES-256 pour les pièces et les clés de session. |
| **Journalisation** | Traçabilité des accès et des actions critiques | Système de logs horodatés (IP, ID utilisateur, action, horodatage UTC) sans injection de données personnelles claires. |
| **Résilience & Disponibilité** | Continuité d'activité et intégrité de l'information | Conteneurisation Docker, redémarrage automatique en cas de défaillance, sondes /health. |
| **Gestion des Vulnérabilités** | Contrôle des failles applicatives | Validation Pydantic contre les injections SQL, XSS, et protection CORS paramétrée. |

---

## 3. Modèles de Déploiement Homologables DGSSI

* **Niveau 1 : Déploiement Air-Gapped (Sensibilité Maximale)**  
  Serveurs dédiés sans accès Internet. Les modèles LLM et embeddings sont préchargés hors-ligne.
* **Niveau 2 : Cloud Souverain National (Niveau Recommandé pour Collectivités & Ministères)**  
  Hébergement au sein d'infrastructures marocaines accréditées (Maroc Telecom, Inwi, Medasys, etc.) garantissant une localisation géographique 100% marocaine et un raccordement au réseau WAN gouvernemental.
'''

with open(os.path.join(juridique_dir, '04_SECURITE_SOUVERAINETE_DGSSI.md'), 'w', encoding='utf-8') as f:
    f.write(doc4)

print('Dossier Juridique files created successfully.')
