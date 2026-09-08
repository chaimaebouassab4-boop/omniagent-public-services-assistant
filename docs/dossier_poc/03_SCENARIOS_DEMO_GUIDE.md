# 🎬 Guide de Démonstration Live du POC — OmniAgent

Ce guide est destiné aux présentateurs, équipes techniques et jurys d'évaluation. Il fournit le déroulé chronologique étape par étape pour démontrer la valeur d'OmniAgent en 15 minutes.

## ⏱️ Déroulé Synthétique de la Démonstration (15 min)

`
[00:00 - 03:00] : Présentation de l'interface citoyenne & Interaction multilingue
[03:00 - 07:00] : Scénario Démarche Complexe en Darija (Certificat de résidence / Kré)
[07:00 - 10:00] : Scénario État Civil & Digitalisation watiqa.ma (Extrait de naissance)
[10:00 - 13:00] : Dépôt de document, Extraction OCR & Pré-validation
[13:00 - 15:00] : Espace d'administration & Suivi des demandes par l'agent public
`

## 📍 Scénario 1 : Assistance en Darija pour un Certificat de Résidence
* **Contexte :** Un citoyen locataire demande quelles sont les pièces nécessaires pour sa شهادة السكنى alors qu'il n'a pas de facture à son nom.
* **Action :** Poser la question en Darija marocaine.
* **Question suggérée :**
> *شنو الوثائق المطلوبة لشهادة السكنى إلا كنت كاري وما عنديش فاتورة الما والضو بسميتي؟*
* **Comportement attendu du système :**
1. Réponse fluide en Darija marocaine.
2. Détail des pièces officielles : contrat de bail légalisé, quittance de loyer récente, déclaration sur l'honneur du propriétaire accompagnée de sa CIN et de la facture à son nom.
3. Indication claire du tarif légal (20 DH de timbres) et du lieu de dépôt (Annexe administrative / Moqataâ).
* **Point fort à souligner au jury :** Prise en compte immédiate des spécificités administratives marocaines sans jargon rébarbatif.

## 📍 Scénario 2 : Démarche État Civil & Orientation watiqa.ma
* **Contexte :** Un citoyen souhaite obtenir un extrait d'acte de naissance sans se déplacer dans sa ville natale.
* **Action :** Poser la question en Français ou en Arabe.
* **Question suggérée :**
> *Comment puis-je demander mon extrait d'acte de naissance en ligne sans me déplacer ?*
* **Comportement attendu du système :**
1. Explication claire de la plateforme nationale watiqa.ma.
2. Distinguo juridique précis entre l'Extrait et la Copie Intégrale.
3. Information sur les délais de livraison postale (4 à 15 jours ouvrables) et le suivi en ligne.
* **Point fort à souligner au jury :** Orientation vers les plateformes gouvernementales existantes, valorisant les investissements numériques de l'État.

## 📍 Scénario 3 : Téléversement & Analyse Documentaire (Document AI)
* **Contexte :** Le citoyen téléverse sa Carte Nationale d'Identité Électronique (CNIE) ou un justificatif.
* **Action :** Déposer un fichier PDF ou image de test via l'interface de chat.
* **Comportement attendu :** Reconnaissance du format, extraction du texte par OCR / PyPDF, et confirmation de prise en charge sans exposer les chemins internes du serveur.

## 📍 Scénario 4 : Espace Agent / Tableau de Bord Administratif
* **Contexte :** L'agent administratif examine les dossiers déposés.
* **Action :** Connexion administrateur et consultation du tableau de bord.
* **Comportement attendu :** Visualisation des métadonnées du dossier, statut d'avancement, et traçabilité complète de l'instruction.
