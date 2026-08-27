# NimbusAI — GPU Cost Optimization Report

**Period:** monthly  
**Baseline spend:** $27,133  
**Optimized spend:** $14,626  
**Projected savings:** $12,507  (**46%**)

## Savings by lever

| Lever | Savings (USD) |
|---|---|
| Inference (cascade/cache/batch) | $1,212 |
| Purchasing (spot/reserved) | $10,040 |
| Right-size util-lies | $655 |
| Kill idle GPUs | $600 |

## Unit economics

- Baseline: **$6.488/1M-token**
- Optimized: **$1.126/1M-token**
- Served: 7,533,027 tokens/day

## GPU efficiency analysis

- **GPU-Util lies detected:** gpu-h100-4, gpu-a10g-1
  - High nvidia-smi % but low MFU → money leaking
  - Action: right-size to cheaper GPU or optimize workload
- **Idle GPUs wasting:** $20/day

## Extension: Reasoning workload impact

- 16.5% of tokens are reasoning queries
- 16.5% of optimized cost
- 94.0% of energy consumption
- Recommendation: cap reasoning requests or route to batch tier

## Extension: Cache economics

- Cache hit rate: 100.0%
- Cache break-even achieved: True
- Write cost amortized over 1.0× reads

## Sustainability

- Energy per query: 0.24 Wh
- Carbon per query: 0.091 gCO2e
- Cheapest+cleanest region: europe-north1

_Figures are June-2026 as-of snapshots; re-baseline before acting._