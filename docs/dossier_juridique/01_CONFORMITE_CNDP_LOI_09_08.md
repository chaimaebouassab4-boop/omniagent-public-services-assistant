# ⚖️ Dossier Juridique — Conformité CNDP & Loi 09-08

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
