'''app/tools/email_tools.py - Email tool functions'''
def send_email(to: str, subject: str, body: str) -> bool:
    '''Mock send email'''
    print(f"[MOCK EMAIL] To: {to}, Subject: {subject}, Body: {body[:50]}...")
    return True

def get_inbox(unread_only: bool = True) -> list:
    '''Mock get emails'''
    return [
        {'from': 'boss@company.com', 'subject': 'Project deadline', 'unread': True},
        {'from': 'client@xyz.com', 'subject': 'New requirements', 'unread': False}
    ]

