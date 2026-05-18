The following project already exists and is working. Apply ONLY these 4 small fixes. Do not regenerate any other files.

---

## FIX 1 — `.env.example` and `app/config.py`

In `.env.example`, rename:
```
# OLD
MAX_AGENT_ITERATIONS=3

# NEW
MAX_REWRITE_ATTEMPTS=2
```

In `app/config.py`, rename the corresponding field:
```python
# OLD
max_agent_iterations: int = 3

# NEW
max_rewrite_attempts: int = 2
```

Then update any reference to `max_agent_iterations` in the codebase (likely in `app/graph/edges.py`) to use `max_rewrite_attempts` from settings instead of the hardcoded value `2`.

---

## FIX 2 — `app/api/routes/chat.py`

In the `/chat` response, replace the `tools_used` field with `pipeline` and `rewrite_count`:

```python
# OLD response dict
return {
    "response": result["generation"],
    "language": result["language"],
    "artifact_references": result["retrieved_docs"],
    "tools_used": [f"corrective_rag (rewrites={result['rewrite_count']})"]
}

# NEW response dict
return {
    "response": result["generation"],
    "language": result["language"],
    "artifact_references": result["retrieved_docs"],
    "pipeline": "corrective_rag",
    "rewrite_count": result["rewrite_count"]
}
```

Also update the Pydantic response model in `app/models.py` accordingly:
```python
# OLD
tools_used: list[str]

# NEW
pipeline: str
rewrite_count: int
```

---

## FIX 3 — Delete `data/museum_general_info.json`

Delete the file `data/museum_general_info.json` — it is unused by any node in the LangGraph pipeline.

Also remove any import or reference to it in the codebase (check `app/config.py` and any route files for a `museum_general_info` path variable).

---

## FIX 4 — `README.md`

Update only these two sections in the existing README:

**In the Environment Variables table**, change:
```
| `MAX_AGENT_ITERATIONS` | `3` | Max tool-call iterations per query |
```
to:
```
| `MAX_REWRITE_ATTEMPTS` | `2` | Max query rewrites in the Corrective RAG loop |
```

**In the `/chat` response example**, change:
```json
"tools_used": ["corrective_rag (rewrites=1)"]
```
to:
```json
"pipeline": "corrective_rag",
"rewrite_count": 1
```

---

## SUMMARY OF FILES TO TOUCH

1. `.env.example` — rename one variable
2. `app/config.py` — rename one field
3. `app/graph/edges.py` — use `settings.max_rewrite_attempts` instead of hardcoded `2`
4. `app/api/routes/chat.py` — fix response dict
5. `app/models.py` — fix response model
6. `data/museum_general_info.json` — DELETE
7. `README.md` — update 2 small sections

Do not touch any other file.
