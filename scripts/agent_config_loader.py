#!/usr/bin/env python3
"""
Agent Config Loader - Load self-improvement config for use in ai_brain.py
This connects the self-improvement system to the actual prediction logic
"""

import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'agent_config.json')


class AgentConfig:
    """Singleton config loader for agent parameters."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config = cls._load_config()
        return cls._instance
    
    @classmethod
    def _load_config(cls) -> dict:
        """Load config from file or return defaults."""
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Defaults
        return {
            'min_edge_threshold': 3.0,
            'confidence_multipliers': {},
            'probability_dampening': 0.0,
            'min_news_sources': 3,
            'lessons_learned': [],
            'version': 0
        }
    
    @classmethod
    def reload(cls):
        """Force reload config from file."""
        cls._config = cls._load_config()
        return cls._config
    
    @property
    def min_edge_threshold(self) -> float:
        return self._config.get('min_edge_threshold', 3.0)
    
    @property
    def confidence_multipliers(self) -> dict:
        return self._config.get('confidence_multipliers', {})
    
    @property
    def probability_dampening(self) -> float:
        return self._config.get('probability_dampening', 0.0)
    
    @property
    def min_news_sources(self) -> int:
        return self._config.get('min_news_sources', 3)
    
    @property
    def lessons_learned(self) -> list:
        return self._config.get('lessons_learned', [])
    
    @property
    def version(self) -> int:
        return self._config.get('version', 0)
    
    def get_confidence_multiplier(self, category: str) -> float:
        """Get confidence multiplier for a specific category."""
        return self.confidence_multipliers.get(category, 1.0)
    
    def apply_dampening(self, probability: float) -> float:
        """Apply probability dampening (move closer to 0.5)."""
        dampening = self.probability_dampening
        if dampening <= 0:
            return probability
        
        # Move probability toward 0.5 by dampening factor
        return probability + (0.5 - probability) * dampening
    
    def get_lessons_for_prompt(self) -> str:
        """Format lessons learned for inclusion in AI prompt."""
        lessons = self.lessons_learned
        if not lessons:
            return ""
        
        text = "\n\nLESSONS FROM PAST MISTAKES (apply these insights):\n"
        for i, lesson in enumerate(lessons, 1):
            text += f"{i}. {lesson}\n"
        
        return text
    
    def should_signal(self, edge: float, category: str = None) -> bool:
        """Check if edge is sufficient to generate a signal."""
        threshold = self.min_edge_threshold
        
        # Apply category-specific multiplier if exists
        if category:
            multiplier = self.get_confidence_multiplier(category)
            # If multiplier < 1, we need MORE edge for this category
            threshold = threshold / multiplier if multiplier > 0 else threshold
        
        return abs(edge) >= threshold


# Convenience function
def get_agent_config() -> AgentConfig:
    return AgentConfig()


if __name__ == "__main__":
    config = get_agent_config()
    
    print("Agent Config Test")
    print("=" * 40)
    print(f"Version: {config.version}")
    print(f"Min Edge Threshold: {config.min_edge_threshold}%")
    print(f"Probability Dampening: {config.probability_dampening}")
    print(f"Min News Sources: {config.min_news_sources}")
    print(f"Confidence Multipliers: {config.confidence_multipliers}")
    print(f"Lessons: {len(config.lessons_learned)}")
    print()
    print("Lessons for prompt:")
    print(config.get_lessons_for_prompt())
    print()
    print("Should signal tests:")
    print(f"  Edge 5%, no category: {config.should_signal(5)}")
    print(f"  Edge 10%, no category: {config.should_signal(10)}")
    print(f"  Edge 15%, no category: {config.should_signal(15)}")
