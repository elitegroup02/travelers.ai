# Real-Time AI Assistant Engine - Proposal & Plan

**Document Created:** December 2025
**Status:** Planning Phase
**Related Project:** travelers.ai (will consume this engine)

---

## Executive Summary

This document outlines a **standalone real-time AI assistant engine** that provides live, proactive AI assistance by continuously processing UI screenshots, user context, and application state. The engine uses a multi-model architecture with concurrent local LLM inference to deliver sub-3-second responses.

**Key Innovation:** Instead of traditional prompt→response interaction, this system runs continuous background inference cycles that proactively prepare information, with an orchestrator deciding what and when to surface to the user.

---

## Table of Contents

1. [Core Concept](#core-concept)
2. [Architecture](#architecture)
3. [Vision Model Selection](#vision-model-selection)
4. [Multi-Model Strategy](#multi-model-strategy)
5. [Technical Implementation](#technical-implementation)
6. [Project Structure](#project-structure)
7. [Implementation Phases](#implementation-phases)
8. [Integration with travelers.ai](#integration-with-travelersai)
9. [Open Questions](#open-questions)

---

## Core Concept

### The Problem with Traditional LLM Interaction

Current LLM interfaces are purely reactive:
1. User asks question
2. System processes
3. System responds
4. Repeat

This creates latency and puts burden on user to know what to ask.

### The Proposed Solution

**Continuous background inference** with:
- Proactive suggestions (AI notices things and offers tips)
- Instant deep responses (pre-computed answers ready when user asks)
- Continuous commentary (AI narrates/comments as user browses)
- Smart anticipation (AI predicts what user needs next)

### User Experience Goals

- **Latency:** 1-3 seconds max for responses
- **Proactivity:** AI surfaces relevant info without being asked
- **Awareness:** AI understands what user is seeing (screenshots)
- **Multilingual:** Support for 35+ languages
- **Non-intrusive:** User controls what surfaces and when

---

## Architecture

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│   │ Chat Panel   │  │ Sidebar Tips │  │ Ambient      │  │ Floating       │  │
│   │ (user talks) │  │ (proactive)  │  │ Overlays     │  │ Windows        │  │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘  │
│          └──────────────────┼──────────────────┴──────────────────┘          │
│                             │                                                │
│                     WebSocket Connection                                     │
│                    (screenshots + state + user messages)                     │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND: REALTIME ENGINE                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      CONTEXT MANAGER                                 │    │
│  │   Screenshots + UI State + User Profile + App Data + History        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│          │                                                │                  │
│          │ (continuous ~1s cycle)                         │ (user message)   │
│          ▼                                                ▼                  │
│  ┌───────────────────┐                        ┌───────────────────────┐     │
│  │ BACKGROUND TRACK  │                        │ USER QUERY TRACK      │     │
│  │                   │                        │ (PRIORITY - PARALLEL) │     │
│  │ ┌───────────────┐ │                        │                       │     │
│  │ │ FAST MODEL    │ │                        │ ┌───────────────────┐ │     │
│  │ │ (Gemma 3 4B)  │ │                        │ │ QUALITY MODEL     │ │     │
│  │ │ "Which lenses │ │                        │ │ (Gemma 3 12B)     │ │     │
│  │ │ should run?"  │ │                        │ │ Full context +    │ │     │
│  │ └───────┬───────┘ │                        │ │ user question     │ │     │
│  │         │         │                        │ └─────────┬─────────┘ │     │
│  │         ▼         │                        │           │           │     │
│  │ ┌───────────────┐ │                        │           │           │     │
│  │ │ BALANCED MODEL│ │                        │           │           │     │
│  │ │ (Gemma 3 4B)  │ │                        │           │           │     │
│  │ │ Run lenses:   │ │                        │           │           │     │
│  │ │ - Context sum │ │                        │           │           │     │
│  │ │ - Proactive   │ │                        │           │           │     │
│  │ │ - Prediction  │ │                        │           │           │     │
│  │ └───────┬───────┘ │                        │           │           │     │
│  │         │         │                        │           ▼           │     │
│  │         ▼         │                        │   Stream to Chat      │     │
│  │ ┌───────────────┐ │                        │                       │     │
│  │ │ ORCHESTRATOR  │ │                        └───────────────────────┘     │
│  │ │ "What to show │ │                                                      │
│  │ │  and where?"  │ │                                                      │
│  │ └───────┬───────┘ │                                                      │
│  └─────────┼─────────┘                                                      │
│            │                                                                 │
│            ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    OUTPUT ROUTER                                     │   │
│   │   Sidebar ← Tips    Ambient ← Overlays    Chat ← Thinking bubbles   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Background Inference Cycle

```
Timeline (every ~1 second when active):

T=0.0s ─► Context snapshot captured
         • Screenshot from frontend
         • Current UI state (screen, selections, scroll)
         • User profile and preferences
         • Application-specific data (cached)
         │
         ▼
T=0.1s ─► FAST MODEL: "Given this context, which lenses should run?"
         • Input: Compressed context summary
         • Output: ["context_summary", "proactive_tip"] or ["prediction"] or []
         • Budget: 50 tokens max, ~0.3s
         │
         ▼
T=0.4s ─► BALANCED MODEL: Run selected lenses in batch
         • Each lens has specific prompt template
         • Budget: 100 tokens per lens, ~1.5s total
         • Lenses run in parallel (batched)
         │
         ▼
T=1.9s ─► ORCHESTRATOR: "What should surface and where?"
         • Input: All lens outputs
         • Output: {"sidebar": "...", "ambient": null, "chat_bubble": "..."}
         • Can be rule-based or LLM-powered (hybrid)
         │
         ▼
T=2.4s ─► Results pushed to frontend via WebSocket
         │
         ▼
T=3.0s ─► New cycle begins (or earlier if significant UI change)
```

### User Query Handling (Parallel Track)

When user sends a message, it **immediately** goes to quality model:

```
User Message ──► Direct to Gemma 3 12B
                 │
                 ├─► Context: Screenshot + UI state + conversation history
                 │
                 ├─► Optional: Include latest background lens outputs as "notes"
                 │
                 └─► Stream response directly to Chat panel

Background cycle continues independently - no waiting.
```

---

## Vision Model Selection

### Research Findings (December 2025)

**llama.cpp Vision Support:**
- libmtmd introduced April 2025 for multimodal support
- Requires: main GGUF + mmproj (multimodal projector) GGUF
- Tools: `llama-mtmd-cli`, `llama-server` with vision

### Model Comparison

| Model | Size | llama.cpp | Languages | Tool Use | VRAM (Q4) | Status |
|-------|------|-----------|-----------|----------|-----------|--------|
| **Gemma 3** | 4B/12B/27B | **YES** | 35+ | **YES** | 3/7/15GB | **RECOMMENDED** |
| Qwen2.5-VL | 7B-72B | Partial | 29 | YES | 5GB+ | Large |
| Qwen3-VL | 8B | **BROKEN** | 32 | Unknown | 5GB | KV cache bugs |
| LLaMA 3.2 Vision | 11B/90B | YES | Limited | Limited | 7/50GB | Working |
| InternVL3 | 8B-78B | Unknown | Unknown | YES | Varies | SOTA |

### Qwen3-VL Issues (Not Recommended)

| Issue | GitHub | Impact |
|-------|--------|--------|
| KV Cache Bug | [#17200](https://github.com/ggml-org/llama.cpp/issues/17200) | Second request fails |
| GPU Utilization | [#16895](https://github.com/ggml-org/llama.cpp/issues/16895) | Max 80%, 60% slower |
| Garbage Output | [#16960](https://github.com/ggml-org/llama.cpp/issues/16960) | 30B produces garbage |
| Conversion | [#16605](https://github.com/ggml-org/llama.cpp/issues/16605) | Architecture error |

### Recommendation: Gemma 3

**Why:**
- Confirmed working with llama.cpp
- 35+ languages (trained on 140)
- Function calling support
- 128k context window
- Good size options for 16GB VRAM
- Pre-quantized GGUF: [ggml-org/gemma-3 collection](https://huggingface.co/collections/ggml-org/gemma-3-67d126315ac810df1ad9e913)

---

## Multi-Model Strategy

### Hardware Target

- **GPU:** RTX 5080 Laptop (16GB VRAM)
- **Throughput:** 60-100+ tok/s expected on Gemma 3 4B

### Model Stack

| Model | VRAM | Role | Port |
|-------|------|------|------|
| Gemma 3 4B-IT (Vision) | ~3GB | Fast orchestration, screenshot analysis | :8081 |
| Gemma 3 12B-IT (Vision) | ~7GB | Quality conversations, complex reasoning | :8082 |
| **Total Active** | ~10GB | + KV cache headroom | |

### Model Management: llama-swap

Using [llama-swap](https://github.com/mostlygeek/llama-swap) for concurrent model management:

- **Groups feature:** Run multiple models simultaneously
- **Hot-swap:** Can bring in 27B when needed
- **OpenAI-compatible API:** Easy integration
- **TTL management:** Auto-unload idle models

**Config example:**
```yaml
models:
  gemma-4b-fast:
    cmd: llama-server -m gemma-3-4b-it.gguf --mmproj mmproj.gguf -ngl 99 --port ${PORT}
    ttl: 300

  gemma-12b-quality:
    cmd: llama-server -m gemma-3-12b-it.gguf --mmproj mmproj.gguf -ngl 99 --port ${PORT}
    ttl: 300

groups:
  concurrent:
    - gemma-4b-fast
    - gemma-12b-quality
```

---

## Technical Implementation

### Lens System

"Lenses" are specialized prompt templates that extract specific insights:

| Lens | Purpose | Output |
|------|---------|--------|
| `context_summary` | What is the user looking at? | 2-3 sentence summary |
| `proactive_tip` | What would help right now? | Actionable suggestion |
| `prediction` | What will user want next? | List of likely actions |
| `comparison` | How does this compare? | Contextual comparison |
| `warning` | Any concerns? | Weather, crowds, closures |
| `deep_dive` | Historical/interesting facts | Fun facts, trivia |

### Orchestrator Logic

**Phase 1 (MVP):** Rule-based
```python
def should_surface(lens_output, confidence, user_activity):
    if confidence < 0.7:
        return None
    if user_activity == "typing":
        return None  # Don't interrupt
    if lens_output.type == "warning":
        return "ambient"  # Always show warnings
    if time_since_last_surface < 10:
        return None  # Rate limit
    return "sidebar"
```

**Phase 2:** Small LLM judge (Gemma 3 4B)
```
Given these lens outputs and user context, what should appear?
Output JSON: {"sidebar": "...", "ambient": "...", "chat": null}
```

**Phase 3:** Hybrid with confidence routing

### Connection Protocol

**WebSocket** (recommended over SSE):
- Bidirectional (needed for screenshots + user input)
- Lower latency
- Better for real-time updates

**Message Types:**
```typescript
// Frontend → Backend
interface ContextUpdate {
  type: "context_update";
  screenshot: string;  // base64
  ui_state: UIState;
  timestamp: number;
}

interface UserMessage {
  type: "user_message";
  content: string;
  timestamp: number;
}

// Backend → Frontend
interface AssistantOutput {
  type: "assistant_output";
  target: "sidebar" | "ambient" | "chat";
  content: string;
  confidence: number;
  lens_source?: string;
}

interface StreamChunk {
  type: "stream_chunk";
  target: "chat";
  content: string;
  done: boolean;
}
```

### Caching Strategy

**Two-Layer Caching:**

1. **LLM-Specific Cache** (in engine)
   - KV cache persistence
   - Common context prefix caching
   - Lens output deduplication

2. **Application-Specific Cache** (in travelers.ai)
   - Redis for POI/trip data
   - User preference caching
   - Scraped data caching

---

## Project Structure

### Standalone Engine (Recommended)

The real-time AI engine should be a **separate project** that can be consumed by any application:

```
cortex/  (or similar name)
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Engine configuration
│   │   ├── connection.py       # WebSocket server
│   │   └── cache.py            # LLM-specific caching
│   │
│   ├── context/
│   │   ├── __init__.py
│   │   ├── manager.py          # Context aggregation
│   │   ├── screenshot.py       # Screenshot processing
│   │   └── state.py            # UI state handling
│   │
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── scheduler.py        # Background cycle scheduler
│   │   ├── llama_client.py     # llama-swap/llama.cpp client
│   │   └── batch.py            # Batched inference
│   │
│   ├── lenses/
│   │   ├── __init__.py
│   │   ├── base.py             # Base lens class
│   │   ├── context_summary.py
│   │   ├── proactive_tip.py
│   │   ├── prediction.py
│   │   └── registry.py         # Lens registration
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── rules.py            # Rule-based orchestration
│   │   ├── llm_judge.py        # LLM-powered orchestration
│   │   └── hybrid.py           # Combined approach
│   │
│   ├── output/
│   │   ├── __init__.py
│   │   ├── router.py           # Route to correct UI target
│   │   └── formatter.py        # Format output per target
│   │
│   └── adapters/
│       ├── __init__.py
│       └── base.py             # Plugin interface for apps
│
├── config/
│   ├── llama-swap.yaml         # Model configuration
│   └── default.yaml            # Engine defaults
│
├── tests/
├── pyproject.toml
└── README.md
```

### Integration with travelers.ai

```
travelers.ai/
├── packages/
│   └── api/
│       └── src/
│           └── travelers_api/
│               ├── ... (existing code)
│               └── cortex_adapter/     # NEW
│                   ├── __init__.py
│                   ├── adapter.py      # Implements cortex adapter interface
│                   ├── lenses/         # Travel-specific lenses
│                   │   ├── poi_tip.py
│                   │   ├── itinerary_suggestion.py
│                   │   └── trip_warning.py
│                   └── context.py      # Travel-specific context enrichment
```

---

## Implementation Phases

### Phase 1: Foundation (MVP Proof of Concept)

**Goal:** Prove the concept works with minimal implementation

1. Set up llama-swap with Gemma 3 4B
2. Create basic WebSocket server
3. Implement screenshot → single inference → response
4. No orchestrator, no lenses - just direct vision Q&A
5. Simple test frontend (HTML page with screenshot upload)

**Success Criteria:** Can send screenshot, get relevant response in <3s

### Phase 2: Background Cycle

**Goal:** Implement continuous background inference

1. Add context manager (screenshot + state aggregation)
2. Implement inference scheduler (1-second cycle)
3. Add 2-3 basic lenses (context_summary, proactive_tip)
4. Rule-based orchestrator (confidence threshold)
5. Output router to multiple UI targets

**Success Criteria:** Proactive tips appear without user asking

### Phase 3: Multi-Model

**Goal:** Add quality model for conversations

1. Add Gemma 3 12B via llama-swap groups
2. Implement parallel user query track
3. Add conversation history management
4. Streaming responses to chat

**Success Criteria:** Can chat while background cycle runs

### Phase 4: Orchestrator Intelligence

**Goal:** Smart decisions about what to surface

1. Implement LLM-powered orchestrator
2. Add confidence scoring
3. Add user activity awareness (don't interrupt typing)
4. Rate limiting and deduplication
5. User preference learning

**Success Criteria:** AI doesn't feel annoying/intrusive

### Phase 5: Plugin System

**Goal:** Make engine generalizable

1. Define adapter interface
2. Create travelers.ai adapter with domain-specific lenses
3. Document plugin API
4. Example adapters for other domains

**Success Criteria:** Can use engine for non-travel apps

### Phase 6: Infrastructure (Last)

**Goal:** Production hardening

1. Health checks (models loaded, memory, GPU)
2. Request logging with correlation IDs
3. Rate limiting
4. Error handling and recovery
5. Metrics and monitoring

---

## Integration with travelers.ai

### How travelers.ai Consumes the Engine

```python
# travelers_api/cortex_adapter/adapter.py

from cortex.adapters.base import BaseAdapter
from cortex.lenses import Lens

class TravelersAdapter(BaseAdapter):
    """Travel-specific adapter for cortex engine."""

    def __init__(self, poi_service, trip_service, cache_service):
        self.poi_service = poi_service
        self.trip_service = trip_service
        self.cache = cache_service

    async def enrich_context(self, base_context: dict) -> dict:
        """Add travel-specific data to context."""
        context = base_context.copy()

        # Add current trip if user has one active
        if user_id := context.get("user_id"):
            active_trip = await self.trip_service.get_active_trip(user_id)
            if active_trip:
                context["active_trip"] = active_trip
                context["trip_pois"] = await self.trip_service.get_pois(active_trip.id)

        # Add nearby POI data if we know location
        if coords := context.get("current_location"):
            nearby = await self.poi_service.get_nearby_pois(coords.lat, coords.lng)
            context["nearby_pois"] = nearby

        return context

    def get_custom_lenses(self) -> list[Lens]:
        """Return travel-specific lenses."""
        return [
            POITipLens(),
            ItinerarySuggestionLens(),
            TripWarningLens(),
            LocalInsightLens(),
        ]
```

### Travel-Specific Lenses

```python
# travelers_api/cortex_adapter/lenses/poi_tip.py

class POITipLens(Lens):
    name = "poi_tip"

    def get_prompt(self, context: dict) -> str:
        poi = context.get("current_poi")
        if not poi:
            return None  # Don't run this lens

        return f"""
        The user is viewing {poi['name']} ({poi['type']}).

        POI Details:
        - Built: {poi.get('year_built', 'Unknown')}
        - Architect: {poi.get('architect', 'Unknown')}
        - Visit Duration: {poi.get('estimated_visit_duration', 60)} minutes

        Give ONE practical tip that would help someone visiting this place.
        Keep it under 30 words. Be specific to this POI.
        """

    def get_target(self) -> str:
        return "ambient"  # Shows as overlay near POI
```

---

## Open Questions

### To Be Decided

1. **Project Name:** What should the standalone engine be called?
   - Options: cortex, herald, lens, copilot-engine, assist

2. **Repository Structure:** Monorepo or separate repos?
   - Monorepo: Easier development, single versioning
   - Separate: Cleaner separation, independent releases

3. **WebSocket vs SSE:** Final decision needed
   - WebSocket: Bidirectional, more complex
   - SSE: Simpler, but need separate upload endpoint for screenshots

4. **Screenshot Frequency:** How often to capture?
   - Every 1s during active use?
   - Event-triggered (significant UI changes)?
   - Hybrid?

5. **VRAM Management:** What if 16GB isn't enough?
   - Dynamic model swapping?
   - Reduce to single model?
   - Cloud fallback?

### Research Needed

1. Gemma 3 actual performance on RTX 5080 (need benchmarks)
2. llama-swap stability with concurrent models
3. Screenshot compression impact on vision quality
4. KV cache optimization for repeated contexts

---

## References

### Sources

- [llama.cpp vision support](https://simonwillison.net/2025/May/10/llama-cpp-vision/)
- [llama.cpp GitHub](https://github.com/ggml-org/llama.cpp)
- [llama-swap GitHub](https://github.com/mostlygeek/llama-swap)
- [Gemma 3 announcement](https://huggingface.co/blog/gemma3)
- [Vision Language Models 2025](https://huggingface.co/blog/vlms-2025)
- [Best VLMs 2025 - Koyeb](https://www.koyeb.com/blog/best-multimodal-vision-models-in-2025)

### Qwen3-VL Issues

- [Feature Request #16207](https://github.com/ggml-org/llama.cpp/issues/16207)
- [KV Cache Bug #17200](https://github.com/ggml-org/llama.cpp/issues/17200)
- [GPU Utilization #16895](https://github.com/ggml-org/llama.cpp/issues/16895)
- [llama-cpp-python #2080](https://github.com/abetlen/llama-cpp-python/issues/2080)

---

## Appendix: Existing travelers.ai Backend

### Current State (December 2025)

The travelers.ai backend is a fully functional FastAPI application with:

**28 implemented endpoints:**
- Auth (5): register, login, refresh, me, update
- Cities (4): search, nearby, by-country, detail
- POIs (5): list, search, nearby, detail, enrich
- Trips (10): CRUD + POI management + sharing
- Itineraries (6): generate, get, update, delete, PDF/ICS export
- Shared (1): public trip viewing
- Health (2): health check, root

**Infrastructure:**
- PostgreSQL + PostGIS for spatial data
- Redis caching (30-day TTL)
- 3 LLM providers (local Llama/Qwen3-8B, OpenAI, Anthropic)
- Wikidata/Wikipedia integration for POI enrichment

**Key Files:**
- `packages/api/src/travelers_api/main.py` - App entry
- `packages/api/src/travelers_api/services/llm.py` - LLM abstraction
- `packages/api/src/travelers_api/services/poi_service.py` - POI enrichment
- `packages/api/src/travelers_api/core/config.py` - Configuration

The real-time engine will integrate with this via an adapter, not replace it.
