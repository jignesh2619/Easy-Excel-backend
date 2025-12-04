#!/usr/bin/env python3
"""
Token Usage Analysis Script
Calculates average tokens per request and compares old vs new stats
"""

# Current Stats (from dashboard)
NEW_REQUESTS = 188
NEW_TOKENS = 4_056_809
NEW_SPEND = 5.68

# Previous Stats
OLD_REQUESTS = 179
OLD_TOKENS_ESTIMATED = 3_600_000  # From previous $5.68 charge
OLD_SPEND = 5.68

print("=" * 60)
print("TOKEN USAGE ANALYSIS: OLD vs NEW STATS")
print("=" * 60)

# Calculate averages
new_avg_tokens = NEW_TOKENS / NEW_REQUESTS
old_avg_tokens_estimated = OLD_TOKENS_ESTIMATED / OLD_REQUESTS

print(f"\n📊 NEW STATS (Current)")
print(f"   Total Requests: {NEW_REQUESTS:,}")
print(f"   Total Tokens: {NEW_TOKENS:,}")
print(f"   Average Tokens per Request: {new_avg_tokens:,.0f} tokens")
print(f"   Total Spend: ${NEW_SPEND:.2f}")
print(f"   Cost per Request: ${NEW_SPEND / NEW_REQUESTS:.4f}")

print(f"\n📊 OLD STATS (Previous)")
print(f"   Total Requests: {OLD_REQUESTS:,}")
print(f"   Total Tokens (estimated): {OLD_TOKENS_ESTIMATED:,}")
print(f"   Average Tokens per Request: {old_avg_tokens_estimated:,.0f} tokens")
print(f"   Total Spend: ${OLD_SPEND:.2f}")
print(f"   Cost per Request: ${OLD_SPEND / OLD_REQUESTS:.4f}")

# Calculate differences
request_diff = NEW_REQUESTS - OLD_REQUESTS
request_diff_percent = (request_diff / OLD_REQUESTS) * 100

token_diff = NEW_TOKENS - OLD_TOKENS_ESTIMATED
token_diff_percent = (token_diff / OLD_TOKENS_ESTIMATED) * 100

avg_token_diff = new_avg_tokens - old_avg_tokens_estimated
avg_token_diff_percent = (avg_token_diff / old_avg_tokens_estimated) * 100

print(f"\n📈 COMPARISON")
print(f"   Request Increase: +{request_diff} requests ({request_diff_percent:+.1f}%)")
print(f"   Token Increase: +{token_diff:,} tokens ({token_diff_percent:+.1f}%)")
print(f"   Avg Token/Request Change: {avg_token_diff:+,.0f} tokens ({avg_token_diff_percent:+.1f}%)")

# Calculate what old total would be if using new average
old_total_if_new_avg = OLD_REQUESTS * new_avg_tokens
print(f"\n🔍 ANALYSIS")
print(f"   If old requests used new average: {old_total_if_new_avg:,.0f} tokens")
print(f"   Actual old tokens (estimated): {OLD_TOKENS_ESTIMATED:,}")
print(f"   Difference: {old_total_if_new_avg - OLD_TOKENS_ESTIMATED:+,.0f} tokens")

# Calculate tokens for the 9 new requests
tokens_for_new_requests = NEW_TOKENS - OLD_TOKENS_ESTIMATED
avg_for_new_requests = tokens_for_new_requests / request_diff if request_diff > 0 else 0

print(f"\n🆕 NEW REQUESTS (Last 9)")
print(f"   Requests: {request_diff}")
print(f"   Total Tokens: {tokens_for_new_requests:,}")
print(f"   Average per New Request: {avg_for_new_requests:,.0f} tokens")

# Expected vs Actual
expected_avg = 6000  # From our estimation guide
print(f"\n⚠️  EXPECTED vs ACTUAL")
print(f"   Expected Average (from guide): {expected_avg:,} tokens/request")
print(f"   Actual Average: {new_avg_tokens:,.0f} tokens/request")
print(f"   Ratio: {new_avg_tokens / expected_avg:.2f}x higher than expected")

# Possible reasons
print(f"\n💡 POSSIBLE REASONS FOR HIGH TOKEN USAGE:")
print(f"   1. Very large sheets (50+ columns) → ~8,750 tokens just for sample data")
print(f"   2. Multiple LLM calls per request (action plan + chart generation)")
print(f"   3. Very long text values in cells (even with 300 char truncation)")
print(f"   4. Complex operations requiring extensive context")
print(f"   5. Chart generation adds additional tokens (if charts are requested)")

# Cost breakdown
print(f"\n💰 COST BREAKDOWN (GPT-4o-mini pricing)")
input_tokens_est = int(NEW_TOKENS * 0.9)  # 90% input
output_tokens_est = int(NEW_TOKENS * 0.1)  # 10% output
input_cost = (input_tokens_est / 1_000_000) * 0.15
output_cost = (output_tokens_est / 1_000_000) * 0.60
total_est_cost = input_cost + output_cost

print(f"   Input tokens (90%): {input_tokens_est:,} → ${input_cost:.4f}")
print(f"   Output tokens (10%): {output_tokens_est:,} → ${output_cost:.4f}")
print(f"   Estimated cost: ${total_est_cost:.4f}")
print(f"   Actual cost: ${NEW_SPEND:.2f}")
print(f"   Note: Actual cost suggests different pricing or additional operations")

print("\n" + "=" * 60)







