# Retrieval and conversation state

The deployed default remains `RAG_BACKEND=bm25`. Its scores are not cosine scores.
To activate BGE-M3 dense retrieval, install the optional runtime and build a new index:

```powershell
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-vector.txt
backend/.venv/Scripts/python.exe backend/scripts/build_bge_index.py
$env:RAG_BACKEND = "chroma"
cd backend
.venv/Scripts/python.exe -m uvicorn main:app --port 8000
```

The builder downloads BAAI/bge-m3 if absent. This model requires substantially more
memory than the old 512 MB BM25 deployment; provision the backend accordingly.
The default collection is `public_services_bge_m3_cosine`. Set `CHROMA_PATH` and
`CHROMA_COLLECTION` to override it; use a new collection name for each rebuild.
An existing E5, L2, unknown-model or incomplete index is rejected, never relabelled.
The original `public_services_kb` is preserved. Do not run the old E5 reindex script
to build this collection.
For Docker, build with `--build-arg WITH_VECTOR=true`, provide the completed
collection (image or volume), and set `RAG_BACKEND=chroma` in the runtime environment.
Changing only the environment variable on the lightweight image is insufficient.

Query and document embeddings are normalized, 1024-dimensional BGE-M3 vectors.
Chroma uses cosine distance; similarity is `1 - distance` (range -1 to 1).
Retrieve 20 candidates, filter by procedure before ANN search, deduplicate text,
and retain scores >= max(0.45, best_score - 0.12). Uniformly weak results are
rejected. The floor and margin are initial calibration parameters, not universal
thresholds. Validate them on representative French, Arabic and Darija queries.
Confidence is 60% best score + 40% mean selected score, with a 15% penalty for
single-chunk support; it is an uncalibrated retrieval indicator, not a probability
that an administrative answer is correct. No Chroma failure silently becomes a
fake cosine result. Generation failure returns source extracts explicitly.

### Limites du score de confiance et guide d'interprétation

Le champ `confidence` (valeur entre 0.0 et 1.0) quantifie la qualité du regroupement
documentaire récupéré par BGE-M3. Il doit être interprété selon les principes suivants :

1. **Ce que mesure la confiance** :
   - L'alignement sémantique dense entre l'encodage de la requête et les chunks indexés.
   - La cohérence du groupe de tête : le poids de 40% sur la moyenne des scores pénalise les
     réponses reposant sur un seul passage isolé avec des résultats secondaires disparates.
   - La redondance du support : la pénalité de 15% (`confidence *= 0.85`) s'applique si un seul
     chunk survit au filtrage relatif (`similarity_score >= max(0.45, best - 0.12)`).

2. **Ce que la confiance NE mesure PAS** :
   - **Ce n'est pas une probabilité d'exactitude juridique** : un score de 0.75 ne signifie pas
     que l'information est correcte à 75%. Si la source administrative officielle dans la base est
     incomplète ou si la situation du citoyen relève d'une dérogation non documentée, le modèle LLM
     peut être induit en erreur malgré un score élevé.
   - **Ce n'est pas une mesure d'exhaustivité** : une question demandant la liste exhaustive des
     pièces requises peut obtenir un score de 0.70 sur un chunk résumant seulement les pièces de base.
   - **Incomparabilité avec l'ancien score BM25** : le mode BM25 calculait une heuristique basée sur
     la couverture lexicale des tokens arabes (0.55 base + boost). Le mode Chroma BGE-M3 calcule une
     similarité cosine projetée (1 - distance). Une valeur de 0.68 en BGE-M3 représente un cluster
     sémantique très solide, là où 0.68 en BM25 reflétait une correspondance lexicale moyenne.

3. **Grille de lecture des seuils** :
   - `< 0.45` : Signal insuffisant ou hors-domaine. Rejeté par le plancher (`floor = 0.45`). Le
     système bascule sur le message de clarification ou le fallback local sans hallucination.
   - `0.45 - 0.60` : Signal modéré. Chunks pertinents mais formulation éloignée, question courte
     ou démarche avec peu de données spécifiques.
   - `0.60 - 0.75` : Cluster documentaire dense et hautement pertinent (cas typique des procédures
     bien documentées comme la CIN ou le certificat de résidence).
   - `> 0.75` : Concordance quasi-exacte entre la requête utilisateur et le texte source.

`POST /api/chat/query` exposes `chunks` (content, metadata, similarity_score),
confidence, backend, threshold, candidate_count and fallback_reason. Authenticated
`POST /api/chat/messages` also returns retrieval metadata and `conversationState`.

State snapshots are persisted on user messages, atomically with each exchange.
`GET /api/chat/sessions/{session_id}/state` replays the owner's user turns to verify
state independently of stored snapshots, including old conversations. Unknown or
foreign sessions return 404. Deleted sessions cannot retain a separate stale state.
The replay ignores assistant answers and uploaded-document context. Supporting
documents mentioned by a user are not verified documents. `ready` is reserved for
a future explicit completeness check; conversation text alone never sets it.
Procedure changes reset procedure-specific context; short follow-ups retain it.
Extraction is conservative and rule based; ambiguous user profiles remain unset.

References: [Chroma collection metrics](https://cookbook.chromadb.dev/core/collections/)
and [BGE-M3 model documentation](https://huggingface.co/BAAI/bge-m3).

