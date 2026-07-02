"""
Agentic AI Landscape Tracker - LLM Summarizer
Uses GitHub Copilot SDK to generate brief summaries.
"""

import logging
import time
import uuid
from typing import Optional

from pythonjsonlogger import jsonlogger


# ---------------------------------------------------------------------------
# Structured JSON logging setup
# ---------------------------------------------------------------------------

class _UtcJsonFormatter(jsonlogger.JsonFormatter):
    """JsonFormatter that emits timestamps in UTC ISO-8601 and renames fields."""

    converter = time.gmtime  # Use UTC for all timestamps

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        if "asctime" in log_record:
            log_record["timestamp"] = log_record.pop("asctime")
        if "levelname" in log_record:
            log_record["level"] = log_record.pop("levelname")


class _MergingLoggerAdapter(logging.LoggerAdapter):
    """LoggerAdapter that merges per-call extra fields with the adapter's own extra."""

    def process(self, msg, kwargs):
        merged = dict(self.extra)
        merged.update(kwargs.get("extra") or {})
        kwargs["extra"] = merged
        return msg, kwargs


def _build_base_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_UtcJsonFormatter(
            fmt="%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


_base_logger = _build_base_logger(__name__)


class Summarizer:
    """Generate summaries using GitHub Copilot SDK."""
    
    def __init__(self, correlation_id: str = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.logger = _MergingLoggerAdapter(
            _base_logger, {"correlation_id": self.correlation_id}
        )
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize the Copilot SDK client."""
        try:
            from github_copilot_sdk import CopilotClient
            self.client = CopilotClient()
        except ImportError:
            self.logger.warning("github-copilot-sdk not installed; summaries will use fallback")
            self.client = None
        except Exception as e:
            self.logger.warning("Could not initialize Copilot SDK", extra={"error": str(e)})
            self.client = None
    
    def categorize(self, title: str, content: str) -> str:
        """
        Categorize content as 'Agentic AI' or 'Other'.
        Returns empty string if Copilot SDK unavailable.
        
        Args:
            title: Article title
            content: Article content/excerpt
            
        Returns:
            Category string: 'Agentic AI', 'Other', or '' (if SDK unavailable)
        """
        # Only categorize if Copilot SDK available
        if not self.client:
            return ''
        
        return self._categorize_with_copilot(title, content)
    
    def summarize(self, title: str, content: str, source: str) -> str:
        """
        Generate a 2-3 sentence summary of an AI announcement.
        
        Args:
            title: Article title
            content: Article content/excerpt
            source: Source name (e.g., "Anthropic", "Cursor")
            
        Returns:
            Brief summary string
        """
        if not content:
            return f"New update from {source}: {title}"
        
        # If Copilot SDK available, use it
        if self.client:
            return self._summarize_with_copilot(title, content, source)
        
        # Fallback: extract first meaningful sentences
        return self._fallback_summarize(title, content, source)
    
    def _categorize_with_copilot(self, title: str, content: str) -> str:
        """Categorize content using GitHub Copilot SDK."""
        prompt = f"""Categorize this AI/tech announcement as either 'Agentic AI' or 'Other'.

Agentic AI refers to AI systems that can:
- Autonomously plan and execute multi-step tasks
- Make decisions and take actions on behalf of users
- Use tools, APIs, or interact with environments
- Have memory and context awareness across interactions
- Work as AI agents, autonomous agents, or multi-agent systems

Examples of Agentic AI: AI agents, autonomous coding assistants, multi-agent frameworks, 
tool-using AI systems, AI that can plan and execute workflows.

Examples of Other: General LLMs, image generators, simple chatbots, model updates without 
agent capabilities, infrastructure/platform news.

Title: {title}
Content: {content[:800]}

Respond with ONLY 'Agentic AI' or 'Other':"""
        
        try:
            response = self.client.complete(
                prompt=prompt,
                max_tokens=10,
                temperature=0.1
            )
            category = response.strip()
            # Validate response
            if category in ['Agentic AI', 'Other']:
                return category
            # If response contains the category
            if 'Agentic AI' in category:
                return 'Agentic AI'
            return 'Other'
        except Exception as e:
            self.logger.error("Copilot categorization failed", extra={"error": str(e)})
            return 'Other'
    
    def _summarize_with_copilot(self, title: str, content: str, source: str) -> str:
        """Generate summary using GitHub Copilot SDK."""
        prompt = f"""Summarize this AI/tech announcement in 2-3 concise sentences.
Focus on: what was announced, key capabilities, and why it matters.

Source: {source}
Title: {title}
Content: {content[:1000]}

Summary:"""
        
        try:
            response = self.client.complete(
                prompt=prompt,
                max_tokens=150,
                temperature=0.3
            )
            summary = response.strip()
            return summary if summary else self._fallback_summarize(title, content, source)
        except Exception as e:
            self.logger.error("Copilot summarization failed", extra={"error": str(e)})
            return self._fallback_summarize(title, content, source)
    
    def _fallback_summarize(self, title: str, content: str, source: str) -> str:
        """Fallback summarization when Copilot SDK unavailable."""
        # Clean and truncate content
        content = content.strip()
        
        # Find first sentence(s)
        sentences = []
        for sep in ['. ', '! ', '? ']:
            if sep in content:
                parts = content.split(sep)
                sentences.extend(parts[:2])
                break
        
        if sentences:
            summary = '. '.join(s.strip() for s in sentences[:2] if s.strip())
            if summary and not summary.endswith('.'):
                summary += '.'
            return summary[:300]
        
        # Last resort: truncate content
        return content[:200] + '...' if len(content) > 200 else content


if __name__ == '__main__':
    # Test summarizer
    summarizer = Summarizer()
    test_summary = summarizer.summarize(
        title="Claude 3.5 Sonnet Released",
        content="Anthropic has released Claude 3.5 Sonnet, their most capable model yet. It features improved reasoning, faster response times, and enhanced coding abilities.",
        source="Anthropic"
    )
    summarizer.logger.info("Test summary result", extra={"summary": test_summary})
