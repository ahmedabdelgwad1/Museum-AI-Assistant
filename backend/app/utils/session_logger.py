import json
import os
import time
from datetime import datetime
import logging

from app.rag.vectorstore import get_supabase_client

logger = logging.getLogger(__name__)

class SessionLogger:
    def __init__(self, session_id: str, locale: str):
        self.session_id = session_id  # This is the LiveKit room name
        self.locale = locale
        self.start_time = time.time()
        self.turns = []
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "session_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.current_turn = None
        self.db_session_id = None
        
        # Initialize DB session
        try:
            client = get_supabase_client()
            # 1. Create a dummy visitor
            vis_res = client.table("visitors").insert({"language_preference": locale}).execute()
            visitor_id = vis_res.data[0]["visitor_id"] if vis_res.data else None
            
            # 2. Create a chat session
            sess_res = client.table("chat_sessions").insert({"visitor_id": visitor_id}).execute()
            if sess_res.data:
                self.db_session_id = sess_res.data[0]["session_id"]
        except Exception as e:
            logger.error(f"Failed to init Supabase chat session: {e}")

    def add_turn(self, user_query: str, ai_response: str, latency_seconds: float, generation_time_seconds: float, relevance_score: float = 0.0, contexts: list[str] = None, retrieval_time: float = 0.0, llm_ttft_time: float = 0.0):
        """Records a single Q&A turn with detailed component-level metrics."""
        turn_data = {
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "ai_response": ai_response,
            "latency_seconds": round(latency_seconds, 3),
            "generation_time_seconds": round(generation_time_seconds, 3),
            "relevance_score": round(relevance_score, 3),
            "contexts": contexts or [],
            "retrieval_time": round(retrieval_time, 3),
            "llm_ttft_time": round(llm_ttft_time, 3),
        }
        self.turns.append(turn_data)
        
        # Save to DB
        if self.db_session_id:
            try:
                client = get_supabase_client()
                client.table("interaction_logs").insert({
                    "session_id": self.db_session_id,
                    "question_text": user_query,
                    "answer_text": ai_response,
                }).execute()
            except Exception as e:
                logger.error(f"Failed to log interaction to DB: {e}")
                
        # Save instantly to disk after every interaction!
        self.save()

    def save(self):
        """Saves the entire session to a JSON file and updates DB end_time."""
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Update DB session end_time
        if self.db_session_id:
            try:
                client = get_supabase_client()
                client.table("chat_sessions").update({
                    "end_time": datetime.fromtimestamp(end_time).isoformat()
                }).eq("session_id", self.db_session_id).execute()
            except Exception as e:
                pass
        
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
