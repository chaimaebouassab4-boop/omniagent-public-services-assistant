"""Live multi-turn verification of BGE-M3 retrieval and conversation state."""
import json
import os
import sys
import uuid
from pathlib import Path

# Force UTF-8 on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# Ensure Chroma backend is configured
os.environ["RAG_BACKEND"] = "chroma"
os.environ["CHROMA_COLLECTION"] = "public_services_bge_m3_cosine"

from fastapi.testclient import TestClient
from main import app


def run_live_multiturn():
    session_id = f"test-multiturn-{uuid.uuid4().hex[:8]}"
    print(f"\n========================================================")
    print(f" LIVE MULTI-TURN TEST (BGE-M3 + Conversation State)")
    print(f" Session ID: {session_id}")
    print(f"========================================================\n")

    with TestClient(app) as client:
        # 1. Create a dedicated test user
        user_email = f"citizen-{uuid.uuid4().hex[:6]}@example.com"
        auth_res = client.post(
            "/api/auth/signup",
            json={"email": user_email, "fullName": "Karim Bennani", "password": "password123"}
        )
        assert auth_res.status_code in (200, 201), f"Signup failed: {auth_res.text}"
        token = auth_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        turns = [
            ("Tour 1 - Initial procedure query", "Comment obtenir le certificat de résidence ?"),
            ("Tour 2 - Follow-up documents query", "Et quels documents ?"),
            ("Tour 3 - Follow-up delay/timing query", "Combien de temps ?"),
            ("Tour 4 - Profile qualification (student)", "Et si je suis étudiant ?"),
        ]

        for i, (title, query_text) in enumerate(turns, 1):
            print(f"--------------------------------------------------------")
            print(f" {title}")
            print(f" Message envoyé : \"{query_text}\"")
            print(f"--------------------------------------------------------")

            resp = client.post(
                "/api/chat/messages",
                headers=headers,
                json={"content": query_text, "language": "fr", "sessionId": session_id}
            )
            assert resp.status_code == 201, f"Tour {i} failed: {resp.text}"
            data = resp.json()

            answer = data.get("content", "")
            state = data.get("conversationState") or {}
            backend = data.get("backend", "unknown")
            confidence = data.get("confidence", 0.0)
            sources = data.get("sources", [])
            chunks = data.get("chunks", [])

            print(f"  Backend utilisé : {backend}")
            print(f"  Score confiance : {confidence}")
            print(f"  Sources         : {sources}")
            print(f"  Chunks retenus  : {len(chunks)}")
            if chunks:
                top_scores = [f"{c.get('similarity_score', 0):.3f}" for c in chunks[:3]]
                print(f"  Top similarités : {', '.join(top_scores)}")
            print(f"  Réponse début   : {answer[:140]}...")

            print("\n  [État de conversation retourné (API)] :")
            print(f"    - session_id              : {state.get('session_id')}")
            print(f"    - current_procedure_id    : {state.get('current_procedure_id')}")
            print(f"    - current_procedure_title : {state.get('current_procedure_title')}")
            print(f"    - stage                   : {state.get('stage')}")
            print(f"    - last_user_intent        : {state.get('last_user_intent')}")
            print(f"    - user_type               : {state.get('user_type')}")
            print(f"    - mentioned_documents     : {state.get('mentioned_documents')}")
            print(f"    - turn_count              : {state.get('turn_count')}")

            # Verify GET /api/chat/sessions/{session_id}/state replay
            state_resp = client.get(f"/api/chat/sessions/{session_id}/state", headers=headers)
            assert state_resp.status_code == 200, f"GET state failed: {state_resp.text}"
            replayed_state = state_resp.json()
            assert replayed_state["turn_count"] == i
            assert replayed_state["current_procedure_id"] == "residence_certificate"
            print(f"  Replay GET /state validé : turn_count={replayed_state['turn_count']}, procedure={replayed_state['current_procedure_id']}\n")

        print("========================================================")
        print("  TOUS LES 4 TOURS MULTI-TURN ONT RÉUSSI AVEC SUCCÈS !")
        print("========================================================\n")


if __name__ == "__main__":
    run_live_multiturn()
