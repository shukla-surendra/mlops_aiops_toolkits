# Bedrock — Knowledge Bases (managed RAG)

> Part of the AWS Mastery track. See [PROGRESS.md](../../../PROGRESS.md).
> **Prereq:** [architecture.md](architecture.md), [models-inference.md](models-inference.md).

Spec sections 3, 5. **RAG (Retrieval-Augmented Generation)** grounds a model's answers in *your* documents so it cites facts instead of hallucinating. Bedrock **Knowledge Bases** is the managed version — you point it at data, it builds and maintains the vector index and retrieval.

---

## 1. Why RAG (the mental model)
An FM only knows its training data. To answer over *your* private/changing docs you **retrieve** the relevant chunks and **inject** them into the prompt so the model answers *from the provided context*. RAG = "open-book exam": retrieve the right pages, then generate.

```
question ─► embed ─► vector search (top-k chunks from your docs)
                              │
                              ▼
   prompt = system + retrieved chunks + question ─► FM ─► grounded answer (+ citations)
```

## 2. What Knowledge Bases automates [Documented]
1. **Ingestion:** point it at a data source (**S3**, and connectors for web crawl, Confluence, SharePoint, Salesforce, etc.).
2. **Chunking:** splits documents into passages (fixed-size, semantic, hierarchical, or none).
3. **Embedding:** runs an **embedding model** (Titan/Cohere) to vectorize each chunk.
4. **Vector store:** writes vectors to a store you choose — **OpenSearch Serverless** (default), **Aurora PostgreSQL + pgvector**, Pinecone, Redis, MongoDB, Neptune Analytics.
5. **Sync:** re-ingests on a schedule/trigger as your data changes.

## 3. Querying [Documented]
Two data-plane calls (`bedrock-agent-runtime`):
- **`Retrieve`** — returns the top-k relevant chunks (you do your own generation). Good for custom pipelines.
- **`RetrieveAndGenerate`** — retrieves *and* calls an FM to produce a grounded answer **with citations** in one call. The fastest path to a working RAG chatbot.

```python
import boto3
agent = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
resp = agent.retrieve_and_generate(
    input={"text": "What is our refund policy?"},
    retrieveAndGenerateConfiguration={
        "type": "KNOWLEDGE_BASE",
        "knowledgeBaseConfiguration": {
            "knowledgeBaseId": "KB123",
            "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-opus-4-8",
        },
    },
)
print(resp["output"]["text"])            # grounded answer
print(resp["citations"])                 # source passages
```

## 4. Quality levers (where RAG succeeds or fails)
- **Chunking strategy** — too big = noisy context; too small = lost meaning. Semantic/hierarchical chunking helps for structured docs.
- **Embedding model + top-k** — better embeddings + right k improve recall; too-high k adds noise + cost.
- **Metadata filtering** — attach metadata (tenant, date, doc type) and filter retrieval → per-tenant isolation + relevance.
- **Reranking** — a rerank model reorders retrieved chunks for precision.
- **Contextual grounding Guardrail** — checks the answer is actually supported by the retrieved context (anti-hallucination); see [security.md](security.md).
- **Hybrid search** — combine semantic (vectors) + keyword (BM25) for better recall on names/IDs.

## 5. When Knowledge Bases vs DIY RAG
- **Knowledge Bases** — fastest, managed ingestion/sync/retrieval, native citations, integrates with Agents. Less control over the exact pipeline.
- **DIY** (your own embeddings + OpenSearch/pgvector + orchestration) — full control, portability, custom rerankers/chunkers; more to build and operate. Many teams start on Knowledge Bases and graduate specific pieces to DIY.

---

## Sources
- AWS docs: *Knowledge Bases for Amazon Bedrock*, *RetrieveAndGenerate / Retrieve*, *Supported vector stores*, *Chunking strategies*, *Metadata filtering*, *Reranking*.

---

## Self-check
1. Explain RAG as an "open-book exam" and why it reduces hallucination.
2. List the five things a Knowledge Base automates from raw docs to a queryable index.
3. `Retrieve` vs `RetrieveAndGenerate` — when do you use each?
4. Name three levers to improve RAG answer quality and what each fixes.
5. How would you enforce that tenant A never retrieves tenant B's documents?
