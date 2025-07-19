# Axon Development Roadmap: Phase 14 – Vector+Structured Memory Sync, Tag-Filtered Retrieval, and Long-Term Summary Rotation

This document outlines **Phase 14** of the Axon agent system. Focus areas include synchronizing vector and structured memory, supporting tagged memory retrieval, and handling memory summarization over time.

---

## 🧠 14.1 – Vector + Structured Memory Sync
**Goal:** Bridge semantic (vector) memory and factual (PostgreSQL) memory.

**Design:**
- Every new structured memory entry (e.g., note, fact, task) triggers optional vector embedding
- Embedding includes reference to structured DB ID
- Retrievals return structured + semantic hits

**Workflow:**
1. User inputs memory-worthy message
2. Agent stores to PostgreSQL
3. Optionally embeds message and saves to Qdrant
4. Stores pointer to Qdrant ID in Postgres

---

## 🔖 14.2 – Tag-Based Retrieval Filters
**Goal:** Retrieve memory based on semantic match + context tags.

**Tag Types:**
- Domain: `personal`, `project`, `health`, `goals`
- Role: `jonathan`, `cary`, `agent`
- Time: timestamps and durations

**Query Example:**
> “What did I say last week about the attic project?”

- Filters by speaker = `jonathan`, domain = `project`, timestamp = `last week`
- Runs semantic similarity search within those bounds

---

## 🧾 14.3 – Long-Term Summary Rotation
**Goal:** Keep long-running memory from bloating or repeating.

**Strategy:**
- Monitor message/thread length
- Periodically summarize older conversations
- Replace raw text with brief summaries in structured + embedded memory
- Maintain “pointer map” from summary back to source entries

**Example:**
> “In June, you worked on attic insulation and made steady progress.” → summarizes 50 lines

---

## ✅ Phase 14 Completion Criteria
- Bi-directional memory sync between Qdrant and PostgreSQL
- Tag-filtered semantic search with hybrid scoring (recency + similarity)
- Background summary rotation system for aging memory
- Tests for memory round-tripping and hybrid queries

---

Next: Phase 15 – Persona Awareness, Contextual Voice Switching, and Tone Matching

