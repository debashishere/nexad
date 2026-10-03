-- check_and_reserve_budget.lua
-- Atomic budget delta check and reservation.
--
-- KEYS[1]: org_campaign_spend_key (e.g., "spend:org_123:cmp_456:2026-09-29")
-- ARGV[1]: requested_delta_usd (e.g., "50.00")
-- ARGV[2]: max_allowed_daily_spend (e.g., "500.00")
-- ARGV[3]: ttl_seconds (e.g., 86400)

local current_spend = redis.call('GET', KEYS[1])
if not current_spend then
    current_spend = 0
else
    current_spend = tonumber(current_spend)
end

local delta = tonumber(ARGV[1])
local max_spend = tonumber(ARGV[2])

if (current_spend + delta) > max_spend then
    return {0, tostring(current_spend)} -- Code 0: Policy Violation
else
    local new_spend = current_spend + delta
    redis.call('SET', KEYS[1], tostring(new_spend), 'EX', tonumber(ARGV[3]))
    return {1, tostring(new_spend)} -- Code 1: Approved and Reserved
end
