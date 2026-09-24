# Feature 3: synthetic profiles and notification drafts

The profiles in `backend/data/mock_citizens.json` are entirely synthetic. They are
for automated tests and demos, not for identity or CNSS verification. A larger,
repeatable set can be generated with `generate_mock_citizens(count, seed)` in
`backend/app/services/mock_citizens.py`.

## Profile prompt

Use `MOCK_PROFILE_PROMPT` from `backend/app/services/mock_citizens.py`. Require
the model to return JSON with `full_name`, `cin`, `phone`, `address`, `city`,
`cnss_number`, `cnss_status`, and `synthetic: true`. Check the output against
the local schema before use; never query or claim a government registry match.

## Notification prompt

Use `NOTIFICATION_PROMPT` from `backend/app/services/case_notifications.py`.
Pass the tracking code, canonical status, optional missing document, and
channel (`SMS` or `WhatsApp`). The model returns `{ "fr": "...", "darija": "..." }`.
Review generated text before any real-world delivery. The app currently stores
deterministic notification **drafts** in the case audit trail; it does not send
SMS or WhatsApp messages.

## Sample outputs

| Event | French | Darija |
| --- | --- | --- |
| SUBMITTED | Votre demande MA-2026-000041 a été reçue. Suivez son évolution dans OmniAgent. | توصلنا بالطلب ديالك MA-2026-000041. تابع الحالة ديالو فـ OmniAgent. |
| DOCS_APPROVED | Les pièces de votre demande MA-2026-000041 sont validées. Attendez la convocation. | الوثائق ديال الطلب MA-2026-000041 تصادقو. تسنى الاستدعاء. |
| READY_FOR_PICKUP | Votre document MA-2026-000041 est prêt. Présentez votre reçu et votre CIN au guichet. | الوثيقة ديالك MA-2026-000041 واجدة. جيب الوصل ولاكارط ناسيونال للشباك. |
| Missing Facture | Dossier MA-2026-000041 : pièce manquante (Facture). Ajoutez-la dans OmniAgent. | الملف MA-2026-000041: خاص وثيقة (Facture). زيدها فـ OmniAgent. |
