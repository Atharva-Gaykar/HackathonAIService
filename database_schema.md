# Database Schema — Voice Chat (STT/TTS) System

## 1. `users`

| Column | Type | Notes |
|---|---|---|
| id | PK | |

---

## 2. `threads`

Represents a conversation session — groups multiple messages together.

| Column | Type | Notes |
|---|---|---|
| id | PK | e.g. `thread_abc` |
| user_id | FK → users.id | |
| created_at | timestamp | session start |

---

## 3. `messages`

One row per audio event (STT input turn or TTS output turn). The `type` column determines which direction the conversion runs.

| Column | Type | Notes |
|---|---|---|
| id | PK | maps to filename, e.g. `msg_<id>` |
| thread_id | FK → threads.id | groups this turn into a conversation |
| user_id | FK → users.id | denormalized — avoids a join for ownership checks |
| type | enum: `stt` \| `tts` | direction of conversion |
| audio_storage_path | text | S3/Supabase path |
| text_content | text | transcript (STT output) or source text (TTS input) |
| created_at | timestamp | for ordering turns within a thread |

**How `type` works:**
- `type = stt` → `audio_storage_path` is the input, `text_content` is the model output (transcript)
- `type = tts` → `text_content` is the input, `audio_storage_path` is the model output (generated audio)

---


#  Sambhodi here you need to handle the insertion part .
## S3 / Supabase Bucket Layout

```
bucket/
└── user_id_123/
    ├── stt/
    │   └── thread_abc/
    │       └── msg_<id>.wav      ← input (spoken query)
    │
    └── tts/
        └── thread_abc/
            └── msg_<id>.wav      ← output (spoken response)
```

- `audio_storage_path` in the `messages` table maps directly to the file path here, joined by `id`.
- Split by `stt/` and `tts/` at the top level (not by thread) so each pipeline can have independent lifecycle/retention rules.
- `thread_abc/` nested underneath keeps all audio for one conversation together for easy per-thread cleanup or export.
