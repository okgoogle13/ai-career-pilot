"""
Firebase Firestore Client Wrapper
Handles all database operations for the Personal AI Career Co-Pilot.
"""

from typing import Dict, Any, Optional, List
import google.cloud.firestore
from datetime import datetime
import json

class FirestoreClient:
    """
    Wrapper class for Firestore operations with error handling and logging.
    """
    
    def __init__(self, db: google.cloud.firestore.Client):
        """
        Initialize the Firestore client wrapper.
        
        Args:
            db: Initialized Firestore client instance
        """
        self.db = db
        self.profiles_collection = db.collection('profiles')
        self.documents_collection = db.collection('generated_documents')
        self.jobs_collection = db.collection('job_opportunities')
    
    async def get_user_profile(self, user_id: str = "primary_user") -> Dict[str, Any]:
        """
        Retrieve user profile from Firestore.
        
        Args:
            user_id: User identifier (default: "primary_user" for single-user app)
            
        Returns:
            User profile dictionary
        """
        try:
            doc_ref = self.profiles_collection.document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                profile_data = doc.to_dict()
                print(f"Retrieved profile for user: {user_id}")
                return profile_data
            else:
                print(f"No profile found for user: {user_id}")
                return self._get_default_profile()
                
        except Exception as e:
            print(f"Error retrieving user profile: {str(e)}")
            return self._get_default_profile()
    
    async def update_user_profile(self, profile_data: Dict[str, Any], 
                                user_id: str = "primary_user") -> bool:
        """
        Update user profile in Firestore.
        
        Args:
            profile_data: Updated profile information
            user_id: User identifier
            
        Returns:
            Success boolean
        """
        try:
            doc_ref = self.profiles_collection.document(user_id)
            
            # Add timestamp for tracking
            profile_data['lastUpdated'] = datetime.utcnow()
            
            doc_ref.set(profile_data, merge=True)
            print(f"Profile updated for user: {user_id}")
            return True
            
        except Exception as e:
            print(f"Error updating user profile: {str(e)}")
            return False
    
    async def save_generated_document(self, document_data: Dict[str, Any], 
                                    user_id: str = "primary_user") -> Optional[str]:
        """
        Save generated document to Firestore for history tracking.
        
        Args:
            document_data: Generated document information
            user_id: User identifier
            
        Returns:
            Document ID if successful, None otherwise
        """
        try:
            # Prepare document for storage
            doc_to_store = {
                'userId': user_id,
                'jobTitle': document_data.get('job_title', ''),
                'company': document_data.get('company', ''),
                'documentType': document_data.get('document_type', 'resume'),
                'themeId': document_data.get('theme_id', 'theme1'),
                'toneOfVoice': document_data.get('tone_of_voice', 'professional'),
                'generatedContent': document_data.get('generated_markdown', ''),
                'atsAnalysis': document_data.get('ats_analysis', {}),
                'createdAt': datetime.utcnow(),
                'status': 'completed'
            }
            
            # Add document to collection
            doc_ref = self.documents_collection.add(doc_to_store)
            document_id = doc_ref[1].id
            
            print(f"Document saved with ID: {document_id}")
            return document_id
            
        except Exception as e:
            print(f"Error saving generated document: {str(e)}")
            return None
    
    async def get_document_history(self, user_id: str = "primary_user", 
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve user's document generation history.
        
        Args:
            user_id: User identifier
            limit: Maximum number of documents to retrieve
            
        Returns:
            List of generated documents
        """
        try:
            query = (self.documents_collection
                    .where('userId', '==', user_id)
                    .order_by('createdAt', direction=google.cloud.firestore.Query.DESCENDING)
                    .limit(limit))
            
            docs = query.stream()
            history = []
            
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['id'] = doc.id
                history.append(doc_data)
            
            print(f"Retrieved {len(history)} documents for user: {user_id}")
            return history
            
        except Exception as e:
            print(f"Error retrieving document history: {str(e)}")
            return []
    
    async def save_job_opportunity(self, job_data: Dict[str, Any]) -> Optional[str]:
        """
        Save job opportunity from job scouting flow.
        
        Args:
            job_data: Job opportunity information
            
        Returns:
            Job ID if successful, None otherwise
        """
        try:
            # Prepare job data for storage
            job_to_store = {
                'title': job_data.get('job_title', ''),
                'company': job_data.get('company', ''),
                'url': job_data.get('url', ''),
                'description': job_data.get('description', ''),
                'deadline': job_data.get('deadline'),
                'source': job_data.get('source', ''),
                'status': 'discovered',
                'createdAt': datetime.utcnow(),
                'reminderCreated': job_data.get('reminder_created', False)
            }
            
            # Check if job already exists to avoid duplicates
            existing_query = (self.jobs_collection
                            .where('url', '==', job_to_store['url'])
                            .limit(1))
            
            existing_docs = list(existing_query.stream())
            
            if existing_docs:
                print(f"Job already exists: {job_to_store['title']}")
                return existing_docs[0].id
            
            # Add new job opportunity
            doc_ref = self.jobs_collection.add(job_to_store)
            job_id = doc_ref[1].id
            
            print(f"Job opportunity saved with ID: {job_id}")
            return job_id
            
        except Exception as e:
            print(f"Error saving job opportunity: {str(e)}")
            return None
    
    async def get_job_opportunities(self, status: str = None, 
                                  limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieve job opportunities from the database.
        
        Args:
            status: Filter by status (optional)
            limit: Maximum number of jobs to retrieve
            
        Returns:
            List of job opportunities
        """
        try:
            query = self.jobs_collection.order_by('createdAt', 
                                                 direction=google.cloud.firestore.Query.DESCENDING)
            
            if status:
                query = query.where('status', '==', status)
            
            query = query.limit(limit)
            docs = query.stream()
            
            opportunities = []
            for doc in docs:
                job_data = doc.to_dict()
                job_data['id'] = doc.id
                opportunities.append(job_data)
            
            print(f"Retrieved {len(opportunities)} job opportunities")
            return opportunities
            
        except Exception as e:
            print(f"Error retrieving job opportunities: {str(e)}")
            return []
    
    async def update_job_status(self, job_id: str, status: str, 
                              notes: str = None) -> bool:
        """
        Update the status of a job opportunity.
        
        Args:
            job_id: Job document ID
            status: New status ('discovered', 'applied', 'interviewing', 'closed')
            notes: Optional notes
            
        Returns:
            Success boolean
        """
        try:
            doc_ref = self.jobs_collection.document(job_id)
            
            update_data = {
                'status': status,
                'lastUpdated': datetime.utcnow()
            }
            
            if notes:
                update_data['notes'] = notes
            
            doc_ref.update(update_data)
            print(f"Job status updated: {job_id} -> {status}")
            return True
            
        except Exception as e:
            print(f"Error updating job status: {str(e)}")
            return False
    
    def _get_default_profile(self) -> Dict[str, Any]:
        """
        Return default profile structure when no profile exists.
        
        Returns:
            Default profile dictionary
        """
        return {
            "fullName": "User Name",
            "email": "user@example.com",
            "phone": "+61 400 000 000",
            "location": "Melbourne, VIC",
            "workExperience": [],
            "education": [],
            "skills": [],
            "certifications": [],
            "personalStatement": "",
            "preferences": {
                "defaultTheme": "theme1",
                "defaultTone": "professional"
            },
            "createdAt": datetime.utcnow(),
            "lastUpdated": datetime.utcnow()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Firestore connection.
        
        Returns:
            Health status information
        """
        try:
            # Try to read from a collection
            test_query = self.profiles_collection.limit(1)
            list(test_query.stream())
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "firestore",
                "message": "Connection successful"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "firestore",
                "error": str(e)
            }
