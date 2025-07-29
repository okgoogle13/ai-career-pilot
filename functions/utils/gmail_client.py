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
        Initializes the GmailClient with optional credentials for Gmail API access.
        
        If credentials information is provided, sets up OAuth2 credentials and the Gmail API service client. If not, both credentials and service are set to None, allowing for scenarios such as local testing without API access.
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
        Retrieve unread emails from a specified sender.
        
        Parameters:
            sender (str): The email address to filter unread emails by.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the message ID, subject, and body snippet of an unread email from the sender. Returns an empty list if the Gmail service is not initialized.
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
        Marks the specified email as read by removing the 'UNREAD' label.
        
        Parameters:
            message_id (str): The unique identifier of the email message to mark as read.
        """
        if not self.service:
            return

        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
