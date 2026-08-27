"""M2 — Inference Cost Levers: $/1M-token, batch x cache x cascade (deck §7).

Run: python missions/m2_inference_levers.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num
from finops import pricing, sustainability

# $/1M tokens (input, output) — illustrative 2026.
MODEL_PRICES = {"small": (0.20, 0.40), "large": (3.00, 15.00)}


def run(verbose: bool = True) -> dict:
    rows = load_csv("token_usage.csv")
    base_cost = opt_cost = 0.0
    total_tokens = 0
    cache_reads = 0
    cache_writes = 0
    for r in rows:
        if int(num(r["cached_input_tokens"])) > 0:
            cache_reads += 1
        cache_writes += 1
    avg_cache_reads = cache_reads / cache_writes if cache_writes else 0.0
    cache_write_cost_per_m = 0.05
    cache_enabled = pricing.cache_is_worth_it(avg_cache_reads, cache_write_cost_per_m)
    reasoning_cost = reasoning_tokens = reasoning_wh = 0.0
    regular_cost = regular_tokens = regular_wh = 0.0

    for r in rows:
        inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
        cached = int(num(r["cached_input_tokens"]))
        is_batch = bool(int(num(r["is_batch"])))
        is_reasoning = bool(int(num(r.get("is_reasoning", 0))))
        total_tokens += inp + out

        # BASELINE: naive deployment — everything on the large model, no cache, no batch
        lin, lout = MODEL_PRICES["large"]
        base_cost += pricing.request_cost(inp, out, lin, lout)

        # OPTIMIZED: cascade (route_tier), prompt caching, batch API
        pin, pout = MODEL_PRICES[r["route_tier"]]
        effective_cached = cached if cache_enabled else 0
        opt_cost += pricing.request_cost(inp, out, pin, pout, cached_in=effective_cached, batch=is_batch)

        # Extension 4: Reasoning budget tracking
        wh = sustainability.wh_per_query(inp + out, is_reasoning=is_reasoning)
        req_cost = pricing.request_cost(inp, out, pin, pout, cached_in=effective_cached, batch=is_batch)
        if is_reasoning:
            reasoning_cost += req_cost
            reasoning_tokens += inp + out
            reasoning_wh += wh
        else:
            regular_cost += req_cost
            regular_tokens += inp + out
            regular_wh += wh

    base_pm = pricing.dollars_per_million(base_cost, total_tokens)
    opt_pm = pricing.dollars_per_million(opt_cost, total_tokens)
    savings_pct = (1 - opt_cost / base_cost) * 100 if base_cost else 0.0

    # Extension 4: reasoning analysis
    reasoning_pct_requests = (reasoning_tokens / total_tokens * 100) if total_tokens else 0.0
    reasoning_pct_cost = (reasoning_cost / opt_cost * 100) if opt_cost else 0.0
    reasoning_pct_wh = (reasoning_wh / (reasoning_wh + regular_wh) * 100) if (reasoning_wh + regular_wh) else 0.0

    if verbose:
        print("== M2 Inference Cost Levers ==")
        print(f"requests={len(rows)}  tokens={total_tokens:,}")
        print(f"baseline  : ${base_cost:,.2f}/day   ${base_pm:.3f}/1M-token")
        print(f"optimized : ${opt_cost:,.2f}/day   ${opt_pm:.3f}/1M-token")
        print(f"savings   : {savings_pct:.1f}%  (cascade + caching + batch)")
        print(f"discount stack (batch + 100% cache): {pricing.discount_stack(batch=True, cache_hit_frac=1.0):.3f} of naive")
        print(f"\n[Extension 3] Cache economics:")
        print(f"  Cache hit rate: {avg_cache_reads:.1%}")
        print(f"  Cache break-even: {(1.0 - 0.1):.1f}× reads > ${cache_write_cost_per_m:.3f}/M write cost")
        print(f"  Cache enabled: {cache_enabled}")
        print(f"\n[Extension 4] Reasoning budget:")
        print(f"  {reasoning_pct_requests:.1f}% of tokens are reasoning")
        print(f"  {reasoning_pct_cost:.1f}% of optimized cost")
        print(f"  {reasoning_pct_wh:.1f}% of energy (Wh)")
        regular_wh_per_token = regular_wh / regular_tokens if regular_tokens else 0.0
        reasoning_wh_per_token = reasoning_wh / reasoning_tokens if reasoning_tokens else 0.0
        multiplier = reasoning_wh_per_token / regular_wh_per_token if regular_wh_per_token else 0.0
        print(f"  Energy multiplier: ~{multiplier:.1f}x vs regular")

    return {
        "baseline_daily": round(base_cost, 2), "optimized_daily": round(opt_cost, 2),
        "baseline_per_m": round(base_pm, 3), "optimized_per_m": round(opt_pm, 3),
        "savings_pct": round(savings_pct, 1), "total_tokens": total_tokens,
        "reasoning_pct_requests": round(reasoning_pct_requests, 1),
        "reasoning_pct_cost": round(reasoning_pct_cost, 1),
        "reasoning_pct_wh": round(reasoning_pct_wh, 1),
        "cache_hit_rate": round(avg_cache_reads, 3),
        "cache_enabled": cache_enabled,
    }


if __name__ == "__main__":
    run()
