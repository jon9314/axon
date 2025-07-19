# Axon Development Roadmap: Phase 11 – Vector Search Upgrades, Summarization Memory, and Cross-Thread Recall

This document defines **Phase 11** of the Axon agent system, focused on enhancing vector memory, reducing noise, and enabling memory recall across chat threads.

---

## 📚 11.1 – Vector Search Optimization

**Goal:** Improve precision and performance of Qdrant-powered search.

**Tech Details:**

- Add `tag` and `context` filtering
- Enable recency decay logic in query pipeline
- Support hybrid scoring: `(similarity + recency_weight + context_match)`

**Enhancements:**

- Retrieval API in `memory/vector_handler.py`
- Index metadata schema: `type`, `context`, `speaker`, `timestamp`

**Example Call:**

```python
search_vector("reminder about attic", context="home_project", top_k=5)
```

---

## 🧠 11.2 – Summarized Long-Term Memory

**Goal:** Store condensed versions of long conversations or context threads.

**Trigger Points:**

- End of long chat session
- On explicit `summarize_context` command
- After task completion

**Stored As:**

```yaml
- type: summary
  topic: Greenhouse project
  date: 2025-07-13
  content: >
    Jonathan explored greenhouse materials, asked about airflow, and requested a list of local suppliers.
```

**Stored In:**

- PostgreSQL (structured)
- Optionally embedded in Qdrant

---

## 🔄 11.3 – Cross-Thread Memory Recall

**Goal:** Allow one thread to query or reference relevant memory from others.

**Trigger Methods:**

- Auto: `search_global_memory()` when current thread has no relevant hits
- Manual: `import_summary("Greenhouse project")`

**Safeguards:**

- Only summaries and fact entries are recalled across threads by default
- Full context retrieval must be user-confirmed

---

## 📘 11.4 – UI Indicators (Optional)

**Memory Source Tags:**

- “(From summary of ‘Greenhouse’ thread)”
- “(Imported from past task on 2025-07-05)”

**Config Toggle:** On/off for inline memory source display

---

## ✅ Phase 11 Completion Criteria

- Vector search supports hybrid (semantic + recency + context)
- Long chats or closed sessions are summarized and indexed
- Other threads can access those summaries when needed
- Optional UI hooks show memory provenance

---

Next: Phase 12 – Goal-Aware Planning, Simulated Tools, and Execution Pathways

