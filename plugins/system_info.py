# axon/plugins/system_info.py

import platform
from agent.plugin_loader import plugin

@plugin(
    name="get_os_version",
    description="Return the host operating system version",
    usage="get_os_version()"
)
def get_os_version():
    """
    A simple plugin that returns the current OS version.
    """
    return f"The current OS is: {platform.system()} {platform.release()}"

