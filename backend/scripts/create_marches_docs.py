import os

base_dir = r'c:\Users\21263\OneDrive\Desktop\omnia.agent\omniagent-public-services-assistant'
marches_dir = os.path.join(base_dir, 'docs', 'dossier_marches_publics')
os.makedirs(marches_dir, exist_ok=True)

# 1. GUIDE REPONSE APPEL OFFRES
doc1 = '''# 🏛️ Guide de Réponse aux Marchés Publics & Consultations au Maroc

**Cadre Réglementaire :** Décret n° 2-22-431 du 8 mars 2023 relatif aux marchés publics (entré en vigueur le 1er septembre 2023)  
**Objectif :** Transformer le socle POC + Dossier Juridique en une offre gagnante dès la parution d'un Appel d'Offres (AO) ou d'une Consultation.  

---

## 1. La Règle d'Or : Pourquoi Attendre la Publication du Marché Précis ?

Chaque consultation lancée par une administration publique marocaine (Ministère, ADD, Commune, Région, Établissement Public) dispose d'un dossier d'appel d'offres (DAO) strict comprenant :
1. **L'Avis d'Appel d'Offres :** Fixe l'objet, le lieu, la date limite de dépôt et le cautionnement provisoire.
2. **Le Règlement de Consultation (RC) :** Définit les critères d'évaluation des offres, le barème de notation technique (souvent sur 100 points, seuil éliminatoire à 70 ou 80) et les pièces requises.
3. **Le Cahier des Prescriptions Spéciales (CPS) :** Fixe les clauses administratives et techniques particulières, le périmètre fonctionnel exact, et les pénalités de retard.
4. **Le Bordereau des Prix Unitaires (BPU) & Détail Quantitatif Estimatif (DQE) :** Modèle financier obligatoire pour l'offre de prix.

> [!IMPORTANT]
> **Tenter de rédiger l'offre finale avant d'avoir le RC et le CPS conduit inévitablement à un rejet pour non-conformité.**
> Grâce à notre démarche, dès la parution du CPS, vous n'avez qu'à puiser dans le **Dossier POC** (pour prouver votre solution) et dans le **Dossier Juridique** (pour valider votre conformité légale).

---

## 2. Les Trois Enveloppes Réglementaires (Décret 2-22-431)

Toute soumission sur le Portail des Marchés Publics (*marchespublics.gov.ma*) s'articule autour de 3 volets :

### Enveloppe 1 : Dossier Administratif
* Déclaration sur l'honneur (modèle officiel conforme à l'article 26 du décret 2-22-431).
* Récépissé du cautionnement provisoire (ou attestation de caution bancaire personnelle et solidaire).
* Attestation fiscale délivrée par la DGI (valable pour l'exercice).
* Attestation de régularité CNSS (délivrée depuis moins d'un an).
* Certificat d'immatriculation au Registre de Commerce (Modèle J récent).
* Statuts de la société et pouvoirs conférés au signataire.

### Enveloppe 2 : Dossier Technique & Mémoire Technique
* **Note méthodologique & Compréhension du besoin :** Directement issue de la synthèse exécutive du POC.
* **Architecture technique & Sécurité :** Issue du document d'architecture et de conformité DGSSI/CNDP.
* **Rapport de performance & Faisabilité :** Preuve tangible apportée par le rapport de benchmark (94.3% de précision).
* **CVs des experts et références de projets similaires.**

### Enveloppe 3 : Offre Financière
* Acte d'engagement dûment signé et chiffré.
* BPU et DQE complétés (prix unitaire HT, TVA 20%, montant total TTC).
'''

with open(os.path.join(marches_dir, '01_GUIDE_REPONSE_APPEL_OFFRES.md'), 'w', encoding='utf-8') as f:
    f.write(doc1)

# 2. MATRICE MEMOIRE TECHNIQUE TYPE
doc2 = '''# 📑 Matrice du Mémoire Technique Type — Solution OmniAgent

Ce document constitue le modèle de structure universel pour le **Mémoire Technique** à soumettre dans le cadre d'un marché public de digitalisation ou d'assistance citoyenne IA.

---

## Sommaire Type du Mémoire Technique

1. **Présentation du Soumissionnaire & Compréhension des Enjeux**
   - Compréhension fine du contexte de modernisation de l'administration marocaine.
   - Enjeux de la Loi 55-19 et de la Charte des Services Publics.
   - Présentation de la valeur différentiatrice d'OmniAgent.

2. **Architecture Technique & Choix Technologiques**
   - Description de la pile logicielle (FastAPI, React, ChromaDB, LLaMA/Mistral local).
   - Justification de la robustesse, de la maintenabilité et de l'interopérabilité (API REST standard).
   - Schémas d'architecture globale et flux de données.

3. **Garanties d'Intelligence Artificielle & Absence d'Hallucination**
   - Mécanisme RAG avec découpage sémantique adapté aux textes administratifs.
   - Résultats concrets du banc d'essai (94.3% de précision, 0% d'hallucination).
   - Prise en charge native de la Darija marocaine et de l'Arabe standard.

4. **Sécurité, Souveraineté & Conformité Réglementaire**
   - Respect strict des exigences CNDP (Loi 09-08).
   - Respect des directives de la DGSSI (Directive Nationale de Sécurité des SI - DNSSI).
   - Hébergement souverain garanti sur le territoire national sans flux transfrontalier.

5. **Méthodologie de Déploiement, Conduite du Changement & Planning**
   - Démarche itérative agile (Phases de cadrage, installation pilote, recette fonctionnelle, généralisation).
   - Planning type prévisionnel en 12 semaines.
   - Formation des agents instructeurs et transfert de compétences.

6. **Service Level Agreement (SLA), Support & Maintenance**
   - Niveaux d'engagement de disponibilité (99.5% minimum).
   - Matrice de sévérité des incidents (Bloquant : intervention en 2h, Majeur : 4h, Mineur : 24h).
   - Modalités de maintenance corrective, préventive et évolutive.
'''

with open(os.path.join(marches_dir, '02_MATRICE_MEMOIRE_TECHNIQUE_TYPE.md'), 'w', encoding='utf-8') as f:
    f.write(doc2)

print('Dossier Marches Publics files created successfully.')
