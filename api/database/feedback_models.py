"""SQLAlchemy models for routing feedback collection."""
from sqlalchemy import Column, String, Integer, Float, JSON, TIMESTAMP, Text, Boolean
from datetime import datetime
import uuid

from api.database.connection import Base

# Import tool intentions from single source of truth
from src.rag.tool_intentions import TOOL_INTENTIONS, is_valid_intention, get_fallback_intention


class RoutingFeedback(Base):
    """
    Stores user queries and their routing decisions for fine-tuning data collection.
    
    Each record captures:
    - The original user query
    - What the model predicted (tools + intentions)
    - Optional user correction if routing was incorrect
    - Metadata for filtering and analysis
    """
    __tablename__ = 'routing_feedback'
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Query context
    user_query = Column(Text, nullable=False)
    character_name = Column(String(255), nullable=False)
    campaign_id = Column(String(255), default='main_campaign')
    
    # Model predictions (what the classifier chose)
    predicted_tools = Column(JSON, nullable=False)  # List of {tool, intention, confidence}
    predicted_entities = Column(JSON, nullable=True)  # Extracted entities
    
    # Model metadata
    classifier_backend = Column(String(50), default='local')  # 'local' or 'llm'
    classifier_inference_time_ms = Column(Float, nullable=True)
    
    # User feedback (filled in when user corrects)
    is_correct = Column(Boolean, nullable=True)  # null = not reviewed, True/False = reviewed
    corrected_tools = Column(JSON, nullable=True)  # List of {tool, intention} if user corrected
    feedback_notes = Column(Text, nullable=True)  # Optional user notes
    
    # Timestamps
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    feedback_at = Column(TIMESTAMP, nullable=True)  # When user provided feedback
    
    # Training data status
    exported_for_training = Column(Boolean, default=False, index=True)
    exported_at = Column(TIMESTAMP, nullable=True)
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'user_query': self.user_query,
            'character_name': self.character_name,
            'campaign_id': self.campaign_id,
            'predicted_tools': self.predicted_tools,
            'predicted_entities': self.predicted_entities,
            'classifier_backend': self.classifier_backend,
            'classifier_inference_time_ms': self.classifier_inference_time_ms,
            'is_correct': self.is_correct,
            'corrected_tools': self.corrected_tools,
            'feedback_notes': self.feedback_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'feedback_at': self.feedback_at.isoformat() if self.feedback_at else None,
            'exported_for_training': self.exported_for_training,
        }
    
    def to_training_example(self):
        """
        Convert to training data format for fine-tuning.
        
        Returns the format expected by the joint classifier training:
        {
            "query": "What level is {CHARACTER}?",
            "tool": "character_data",
            "intent": "character_info"
        }
        
        Note: user_query already has placeholders applied at storage time.
        
        If user corrected, uses corrected_tools. Otherwise uses predicted_tools.
        Returns a list (one example per tool selected).
        """
        examples = []
        tools = self.corrected_tools if self.corrected_tools else self.predicted_tools
        
        for tool_info in tools:
            examples.append({
                'query': self.user_query,  # Already has placeholders from storage
                'tool': tool_info['tool'],
                'intent': tool_info['intention'],
                'is_correction': self.corrected_tools is not None
            })
        
        return examples
    
# TOOL_INTENTIONS is imported from src.rag.tool_intentions (single source of truth)
# Re-exported here for backward compatibility with existing imports
