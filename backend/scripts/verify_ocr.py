"""
Quick Verification Script for Gemini Vision OCR and Gemini LLM.
Run:
    python backend/scripts/verify_ocr.py
"""
import sys
from pathlib import Path

# Force UTF-8 encoding on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings

def test_gemini():
    print("=" * 60)
    print("[*] VERIFICATION OCR & GEMINI - OMNIAGENT")
    print("=" * 60)
    
    api_key = settings.google_api_key.strip()
    if not api_key or api_key.startswith("AIzaSy..."):
        print("\n[!] INFO: GOOGLE_API_KEY est actuellement vide dans backend/.env")
        print("Pour activer la reconnaissance OCR (photos, CIN, scans):")
        print("1. Rendez-vous sur https://aistudio.google.com/ pour creer une cle gratuite.")
        print("2. Ouvrez backend/.env et collez votre cle:")
        print("   GOOGLE_API_KEY=AIzaSy...")
        print("3. Relancez cette commande pour verifier !")
        return False
    
    print(f"\n[OK] Cle Google API detectee : {api_key[:6]}...{api_key[-4:]}")
    print(f"[OK] Modele Gemini configure : {settings.gemini_model}")
    print(f"[OK] Provider LLM actuel     : {settings.llm_provider}")
    
    # 1. Test Gemini Text
    print("\n[1/2] Test de connexion a Gemini API...")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        res = model.generate_content("Reponds simplement 'OK' en un mot.")
        print(f"  Reponse Gemini : {res.text.strip()}")
        print("  [OK] Connexion API Gemini validee avec succes!")
    except Exception as exc:
        print(f"  [ERREUR] Echec de connexion Gemini : {exc}")
        return False

    # 2. Test Gemini Vision OCR
    print("\n[2/2] Test du module OCR Vision...")
    try:
        from app.services.document_analyzer import _ocr_with_gemini
        dummy_png = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00'
            b'\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        ocr_result = _ocr_with_gemini(dummy_png, "image/png", api_key, settings.gemini_model)
        print("  [OK] Module OCR Vision operationnel et pret a analyser les images!")
    except Exception as exc:
        print(f"  [ERREUR] Echec du test OCR Vision : {exc}")
        return False

    print("\n" + "=" * 60)
    print("[SUCCES] TOUT EST OPERATIONNEL !")
    print("Votre machine peut desormais lire captures, photos et documents.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_gemini()
