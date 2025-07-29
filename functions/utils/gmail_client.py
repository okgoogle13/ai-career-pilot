"""
Gmail API Client
Handles all interactions with the Gmail API for job scouting.
"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing import List, Dict, Any

class GmailClient:
    """
    Wrapper class for Gmail API operations.
    """

    def __init__(self, credentials_info: Dict[str, str] = None):
        """
        Initialize the Gmail client.

        Args:
            credentials_info: Dictionary with credentials information.
        """
        if credentials_info:
            self.creds = Credentials.from_authorized_user_info(credentials_info, ['https://www.googleapis.com/auth/gmail.readonly'])
            self.service = build('gmail', 'v1', credentials=self.creds)
        else:
            # Handle case where credentials are not provided, e.g., for local testing
            self.creds = None
            self.service = None

    async def get_unread_emails(self, sender: str) -> List[Dict[str, Any]]:
        """
        Get unread emails from a specific sender.

        Args:
            sender: The email address of the sender.

        Returns:
            A list of email dictionaries.
        """
        if not self.service:
            return []

        query = f'is:unread from:{sender}'
        results = self.service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])

        emails = []
        for message in messages:
            msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
            email_data = {
                'id': message['id'],
                'subject': next(header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject'),
                'body': msg['snippet']  # Using snippet for simplicity
            }
            emails.append(email_data)

        return emails

    async def mark_as_read(self, message_id: str):
        """
        Mark an email as read.

        Args:
            message_id: The ID of the message to mark as read.
        """
        if not self.service:
            return

        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
