from prometheus_client import Counter, Gauge

AGENT_TASKS = Counter(
    "agent_tasks_total",
    "Number of tasks processed by agents",
    ["agent_id", "task_type"]
)

AGENT_MEMORY_USAGE = Gauge(
    "agent_memory_bytes",
    "Memory usage by agent",
    ["agent_id"]
) 