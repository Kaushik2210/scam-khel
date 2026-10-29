# Model report

Generated 2026-10-29T01:53:58+00:00 against `https://integrate.api.nvidia.com/v1/`

## NVIDIA models available
- `nvidia/ai-synthetic-video-detector`
- `nvidia/cosmos-reason2-8b`
- `nvidia/embed-qa-4`
- `nvidia/ising-calibration-1.5-31b`
- `nvidia/llama-3.1-nemoguard-8b-content-safety`
- `nvidia/llama-3.1-nemoguard-8b-topic-control`
- `nvidia/llama-3.1-nemotron-51b-instruct`
- `nvidia/llama-3.1-nemotron-70b-instruct`
- `nvidia/llama-3.1-nemotron-safety-guard-8b-v3`
- `nvidia/llama-3.1-nemotron-ultra-253b-v1`
- `nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1`
- `nvidia/llama-3.2-nv-embedqa-1b-v1`
- `nvidia/llama-nemotron-embed-vl-1b-v2`
- `nvidia/llama3-chatqa-1.5-70b`
- `nvidia/mistral-nemo-minitron-8b-8k-instruct`
- `nvidia/nemotron-3-embed-1b`
- `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`
- `nvidia/nemotron-3-super-120b-a12b`
- `nvidia/nemotron-3-ultra-550b-a55b`
- `nvidia/nemotron-3.5-bolt-e4b`
- `nvidia/nemotron-3.5-content-safety`
- `nvidia/nemotron-3.5-embed-1b`
- `nvidia/nemotron-3.5-embed-8b`
- `nvidia/nemotron-3.5-lightning-30b-a3b`
- `nvidia/nemotron-3.5-super-vl-120b-a12b`
- `nvidia/nemotron-4-340b-instruct`
- `nvidia/nemotron-4-340b-reward`
- `nvidia/nemotron-nano-3-30b-a3b`
- `nvidia/nemotron-parse`
- `nvidia/nemotron-parse-2.0`
- `nvidia/neva-22b`
- `nvidia/nv-embedqa-mistral-7b-v2`
- `nvidia/nvclip`
- `nvidia/riva-translate-4b-instruct`
- `nvidia/riva-translate-4b-instruct-v2`
- `nvidia/vila`

## Tier validation
| tier | model | exists | smoke | latency ms | json (prompt) | tools |
|---|---|---|---|---|---|---|
| fast | `nvidia/nemotron-3.5-bolt-e4b` | True | True | 363 | True | True |
| mid | `nvidia/nemotron-3.5-lightning-30b-a3b` | True | True | 581 | True | True |
| deep | `nvidia/nemotron-3-ultra-550b-a55b` | True | True | 1134 | True | True |

**Recommended `STRUCTURED_MODE`: `json_prompt`**

Embeddings: not probed; FTS5 + tactic-sequence similarity is used for retrieval.
