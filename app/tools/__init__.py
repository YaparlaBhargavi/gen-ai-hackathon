# app/tools/__init__.py
"""
Tools module for AI Productivity Assistant.

This module contains various tool integrations including:
- Calendar tools (create_event, list_events)
- Email tools (send_email, get_inbox)
- Notification tools (send_notification)
- MCP tools (mcp_query)

These tools are available for use by the agents.
"""

# Import tools for easy access
# Uncomment as needed when implementing specific features
# from .calendar_tools import create_event, list_events
# from .email_tools import send_email, get_inbox
# from .notification_tools import send_notification
# from .mcp_tools import mcp_query

# Define what's available when importing from tools
__all__ = [
    # 'create_event',
    # 'list_events',
    # 'send_email',
    # 'get_inbox',
    # 'send_notification',
    # 'mcp_query',
]

# Version info
__version__ = "1.0.0"
