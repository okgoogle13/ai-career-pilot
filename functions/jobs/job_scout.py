"""
Scheduled job for scouting job opportunities.
"""
import asyncio
from typing import Dict, Any, List

from firebase_functions import scheduler_fn

from ..utils.gmail_client import GmailClient
from ..utils.calendar_client import CalendarClient

# Initialize utilities
gmail_client = GmailClient()
calendar_client = CalendarClient()

@scheduler_fn.on_schedule(schedule="0 */1 * * *")  # Run every hour
def job_scout_scheduled(event: scheduler_fn.ScheduledEvent) -> None:
    """Scheduled function for job scouting."""

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(job_scout())
        print(f"Job scout completed: {result}")

    except Exception as e:
        print(f"Job scout error: {str(e)}")

async def job_scout() -> Dict[str, Any]:
    """
    Scheduled Genkit flow for monitoring Gmail and creating calendar events.
    Scans for interview invitations and job opportunities.

    Returns:
        {
            "processedEmails": int,
            "eventsCreated": int,
            "status": str
        }
    """

    try:
        # Scan for unread emails from job alert senders
        target_senders = [
            "noreply@s.seek.com.au",
            "noreply@ethicaljobs.com.au",
            "donotreply@jora.com",
            "support@careers.vic.gov.au"
        ]

        processed_emails = 0
        events_created = 0

        for sender in target_senders:
            # Get unread emails from sender
            emails = await gmail_client.get_unread_emails(sender)

            for email in emails:
                # Parse email for job opportunities
                job_opportunities = _extract_job_opportunities(email)

                # Create calendar reminders for each opportunity
                for opportunity in job_opportunities:
                    calendar_event = await calendar_client.create_reminder_event(
                        title=f"Apply: {opportunity['job_title']} - {opportunity['company']}",
                        description=f"Job URL: {opportunity['url']}\nDeadline: {opportunity.get('deadline', 'Not specified')}",
                        reminder_days=2  # Remind 2 days before application deadline
                    )

                    if calendar_event:
                        events_created += 1

                # Mark email as read
                await gmail_client.mark_as_read(email['id'])
                processed_emails += 1

        return {
            "processedEmails": processed_emails,
            "eventsCreated": events_created,
            "status": "success"
        }

    except Exception as e:
        print(f"Error in job_scout flow: {str(e)}")
        # Log the error for better debugging
        # from google.cloud import logging
        # client = logging.Client()
        # logger = client.logger('job_scout_errors')
        # logger.log_struct({'message': f"Error in job_scout flow: {str(e)}"}, severity='ERROR')
        return {
            "processedEmails": 0,
            "eventsCreated": 0,
            "status": f"error: {str(e)}"
        }

def _extract_job_opportunities(email: Dict) -> List[Dict[str, Any]]:
    """Extract job opportunities from email content."""

    opportunities = []
    subject = email.get('subject', '')
    body = email.get('body', '')

    # Simple pattern matching for job opportunities
    # This would be enhanced with more sophisticated NLP
    if any(keyword in subject.lower() for keyword in ['job alert', 'new job', 'opportunities']):
        # Extract basic information (this is a simplified implementation)
        opportunities.append({
            "job_title": subject,
            "company": "Unknown",
            "url": "mailto:example@example.com",  # Would extract actual URLs
            "deadline": None
        })

    return opportunities
