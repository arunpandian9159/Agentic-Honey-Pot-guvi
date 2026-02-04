"""
Detection Metrics for Advanced Scam Detection System.
Tracks prediction performance and calculates accuracy metrics.
"""

from datetime import datetime
from typing import Dict, List, Optional


class DetectionMetrics:
    """Track detection performance metrics."""
    
    def __init__(self):
        self.predictions: List[Dict] = []
    
    def add_prediction(
        self,
        message: str,
        predicted_scam: bool,
        confidence: float,
        actual_scam: Optional[bool] = None,
        scam_type: Optional[str] = None
    ):
        """Add a prediction for tracking."""
        self.predictions.append({
            "message": message[:100],  # Truncate for storage
            "predicted_scam": predicted_scam,
            "confidence": confidence,
            "actual_scam": actual_scam,
            "scam_type": scam_type,
            "timestamp": datetime.now()
        })
    
    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics."""
        
        # Filter predictions with known ground truth
        labeled = [p for p in self.predictions if p["actual_scam"] is not None]
        
        if not labeled:
            return {"error": "No labeled predictions"}
        
        # Calculate confusion matrix
        true_positives = sum(
            1 for p in labeled
            if p["predicted_scam"] and p["actual_scam"]
        )
        true_negatives = sum(
            1 for p in labeled
            if not p["predicted_scam"] and not p["actual_scam"]
        )
        false_positives = sum(
            1 for p in labeled
            if p["predicted_scam"] and not p["actual_scam"]
        )
        false_negatives = sum(
            1 for p in labeled
            if not p["predicted_scam"] and p["actual_scam"]
        )
        
        # Calculate metrics
        total = len(labeled)
        accuracy = (true_positives + true_negatives) / total if total > 0 else 0
        
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0 else 0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0 else 0
        )
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0 else 0
        )
        
        false_positive_rate = (
            false_positives / (false_positives + true_negatives)
            if (false_positives + true_negatives) > 0 else 0
        )
        false_negative_rate = (
            false_negatives / (false_negatives + true_positives)
            if (false_negatives + true_positives) > 0 else 0
        )
        
        return {
            "total_predictions": total,
            "true_positives": true_positives,
            "true_negatives": true_negatives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1_score, 4),
            "false_positive_rate": round(false_positive_rate, 4),
            "false_negative_rate": round(false_negative_rate, 4)
        }
    
    def get_summary(self) -> Dict:
        """Get quick summary of predictions."""
        total = len(self.predictions)
        scams = sum(1 for p in self.predictions if p["predicted_scam"])
        
        return {
            "total_analyzed": total,
            "scams_detected": scams,
            "legitimate": total - scams,
            "avg_confidence": (
                sum(p["confidence"] for p in self.predictions) / total
                if total > 0 else 0
            )
        }
    
    def clear(self):
        """Clear all predictions."""
        self.predictions = []


# Singleton instance for global tracking
detection_metrics = DetectionMetrics()
