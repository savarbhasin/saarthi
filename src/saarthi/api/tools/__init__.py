from saarthi.api.tools import memory, onboarding, outreach, schedule, tasks
from saarthi.api.tools.base import Tool

REGISTRY: dict[str, Tool] = {
    **onboarding.TOOLS,
    **tasks.TOOLS,
    **memory.TOOLS,
    **schedule.TOOLS,
    **outreach.TOOLS,
}
