"""
Google Calendar API Client
Handles all interactions with the Google Calendar API for job scouting.
"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing import Dict, Any
from datetime import datetime, timedelta

class CalendarClient:
    """
    Wrapper class for Google Calendar API operations.
    """

    def __init__(self, credentials_info: Dict[str, str] = None):
        """
        Initialize the Calendar client.

        Args:
            credentials_info: Dictionary with credentials information.
        """
        if credentials_info:
            self.creds = Credentials.from_authorized_user_info(credentials_info, ['https://www.googleapis.com/auth/calendar'])
            self.service = build('calendar', 'v3', credentials=self.creds)
        else:
            self.creds = None
            self.service = None

    async def create_reminder_event(self, title: str, description: str, reminder_days: int) -> Dict[str, Any]:
        """
        Create a reminder event in the user's calendar.

        Args:
            title: The title of the event.
            description: The description of the event.
            reminder_days: The number of days before the event to set a reminder.

        Returns:
            The created event dictionary.
        """
        if not self.service:
            return None

        # Set the event for 'reminder_days' from now
        event_time = datetime.utcnow() + timedelta(days=reminder_days)

        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': event_time.isoformat() + 'Z',
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': (event_time + timedelta(hours=1)).isoformat() + 'Z',
                'timeZone': 'UTC',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        created_event = self.service.events().insert(calendarId='primary', body=event).execute()
        return created_event
