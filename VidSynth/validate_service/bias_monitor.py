"""
Bias Monitor Module
Detects potential bias in generated summaries by comparing semantic similarity
between the video title and the generated summary.
"""

import logging
import os
from typing import Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BiasMonitor:
    """
    Real-time bias detection using semantic similarity.
    """
    
    def __init__(
        self, 
        model_name: str = 'all-MiniLM-L6-v2',
        bias_threshold: float = 0.30
    ):
        """
        Initialize the bias monitor.
        
        Args:
            model_name: Sentence transformer model to use
            bias_threshold: Minimum similarity score (0-1). Scores below indicate bias.
        """
        logger.info(f"Initializing BiasMonitor with model: {model_name}")
        
        try:
            self.model = SentenceTransformer(model_name)
            logger.info("Sentence transformer model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            raise
        
        self.bias_threshold = bias_threshold
        self.model_name = model_name
        
        logger.info(f"BiasMonitor initialized with threshold: {bias_threshold}")
    
    def check_bias(
        self, 
        video_title: str, 
        generated_summary: str,
        summary_type: str = "video"
    ) -> Dict:
        """
        Check for bias by comparing semantic similarity between title and summary.
        
        Args:
            video_title: The title of the YouTube video
            generated_summary: The AI-generated summary
            summary_type: Type of summary ("video" or "comment")
        
        Returns:
            Dictionary with bias detection results
        """
        
        # Input validation
        if not video_title or not video_title.strip():
            logger.warning("Empty video title provided, skipping bias check")
            return self._create_skip_result("Empty video title")
        
        if not generated_summary or not generated_summary.strip():
            logger.warning("Empty summary provided, marking as biased")
            return self._create_biased_result(video_title, generated_summary, 0.0, "Empty summary")
        
        # Handle placeholder messages
        placeholder_messages = [
            "No transcript available",
            "No comments available",
            "Failed to generate",
            "Error generating"
        ]
        
        if any(placeholder in generated_summary for placeholder in placeholder_messages):
            logger.info("Placeholder message detected, skipping bias check")
            return self._create_skip_result("Placeholder message")
        
        try:
            # Generate embeddings
            logger.debug(f"Generating embeddings for title and {summary_type} summary")
            title_embedding = self.model.encode([video_title])
            summary_embedding = self.model.encode([generated_summary])
            
            # Calculate cosine similarity
            similarity_score = cosine_similarity(title_embedding, summary_embedding)[0][0]
            similarity_score = float(similarity_score)
            
            # Determine if biased
            is_biased = similarity_score < self.bias_threshold
            
            logger.info(
                f"{summary_type.capitalize()} Summary - "
                f"Similarity: {similarity_score:.4f}, "
                f"Biased: {is_biased}"
            )
            
            result = {
                "similarity_score": similarity_score,
                "is_biased": is_biased,
                "threshold": self.bias_threshold,
                "summary_preview": generated_summary[:100] + "..." if len(generated_summary) > 100 else generated_summary,
                "video_title": video_title,
                "summary_type": summary_type
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error during bias check: {e}", exc_info=True)
            return self._create_biased_result(
                video_title,
                generated_summary,
                0.0,
                f"Error during check: {str(e)}"
            )
    
    def _create_skip_result(self, reason: str) -> Dict:
        """Create a result for skipped bias checks."""
        return {
            "similarity_score": None,
            "is_biased": False,
            "threshold": self.bias_threshold,
            "summary_preview": None,
            "video_title": None,
            "summary_type": "skipped",
            "skip_reason": reason
        }
    
    def _create_biased_result(
        self, 
        video_title: str, 
        summary: str, 
        score: float,
        reason: str
    ) -> Dict:
        """Create a result indicating bias."""
        return {
            "similarity_score": score,
            "is_biased": True,
            "threshold": self.bias_threshold,
            "summary_preview": summary[:100] + "..." if len(summary) > 100 else summary,
            "video_title": video_title,
            "summary_type": "error",
            "error_reason": reason
        }
    
    def update_threshold(self, new_threshold: float):
        """Update the bias detection threshold."""
        if not 0 <= new_threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        
        logger.info(f"Updating bias threshold from {self.bias_threshold} to {new_threshold}")
        self.bias_threshold = new_threshold


# Singleton instance
_bias_monitor_instance = None

def get_bias_monitor() -> BiasMonitor:
    """Get or create the singleton BiasMonitor instance."""
    global _bias_monitor_instance
    
    if _bias_monitor_instance is None:
        model_name = os.getenv("BIAS_MODEL_NAME", "all-MiniLM-L6-v2")
        threshold = float(os.getenv("BIAS_THRESHOLD", "0.30"))
        
        _bias_monitor_instance = BiasMonitor(
            model_name=model_name,
            bias_threshold=threshold
        )
    
    return _bias_monitor_instance