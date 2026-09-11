# 🛡️ Dossier Juridique & Technique — Sécurité et Souveraineté Numérique DGSSI

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
