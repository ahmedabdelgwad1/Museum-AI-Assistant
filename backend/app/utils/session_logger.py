import json
import os
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SessionLogger:
    def __init__(self, session_id: str, locale: str):
        self.session_id = session_id
        self.locale = locale
        self.start_time = time.time()
        self.turns = []
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "session_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # We will hold state of the current turn
        self.current_turn = None

    def add_turn(self, user_query: str, ai_response: str, latency_seconds: float, generation_time_seconds: float, relevance_score: float = 0.0):
        """Records a single Q&A turn."""
        self.turns.append({
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "ai_response": ai_response,
            "latency_seconds": round(latency_seconds, 3),
            "generation_time_seconds": round(generation_time_seconds, 3),
            "relevance_score": round(relevance_score, 3)
        })
        # Save instantly to disk after every interaction!
        self.save()

    def save(self):
        """Saves the entire session to a JSON file."""
        end_time = time.time()
        duration = end_time - self.start_time
        
        data = {
            "session_id": self.session_id,
            "locale": self.locale,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat(),
            "total_duration_seconds": round(duration, 2),
            "total_turns": len(self.turns),
            "turns": self.turns
        }
        
        filename = os.path.join(self.log_dir, f"session_{self.session_id}.json")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("Session %s logged successfully to %s", self.session_id, filename)
        except Exception as e:
            logger.error("Failed to save session log: %s", e)
