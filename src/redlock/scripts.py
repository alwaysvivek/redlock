# Lua script to release the lock safely.
# It checks if the value in Redis matches the client's token.
# If so, it deletes the key.
# KEYS[1] = resource name
# ARGV[1] = token
RELEASE_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

# Lua script to extend the lock.
# It checks if the value matches the token.
# If so, it updates the PEXPIRE.
# KEYS[1] = resource name
# ARGV[1] = token
# ARGV[2] = additional ttl in milliseconds
EXTEND_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("pexpire", KEYS[1], ARGV[2])
else
    return 0
end
"""
