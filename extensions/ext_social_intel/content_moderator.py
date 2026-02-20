"""
Content Moderator

Advanced content moderation system for social media content.
Provides NSFW detection, spam filtering, hate speech detection,
and content quality assessment for maintaining platform safety
and content standards.

Key Features:
- NSFW content detection and filtering
- Spam detection and prevention
- Hate speech and toxic content identification
- Content quality assessment
- Custom moderation rules and policies
- Real-time content filtering
- User behavior analysis for moderation
"""

import logging
import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import unicodedata

logger = logging.getLogger("SME.SocialIntelligence.ContentModerator")

@dataclass
class ModerationResult:
    """Result of content moderation."""
    content_id: str
    content_type: str  # "text", "image", "video", "mixed"
    moderation_score: float  # 0.0 to 1.0 (higher = more problematic)
    moderation_level: str   # "allow", "flag", "block"
    detected_issues: List[str]
    confidence: float
    suggested_action: str
    metadata: Dict[str, Any]

@dataclass
class UserModerationProfile:
    """User moderation profile for behavior analysis."""
    user_id: str
    violation_history: List[Dict[str, Any]]
    trust_score: float
    risk_level: str
    last_moderation_action: Optional[str]
    moderation_count: int

class ContentModerator:
    """
    Advanced content moderation system for social media content.
    
    Provides NSFW detection, spam filtering, hate speech detection,
    and content quality assessment for maintaining platform safety
    and content standards.
    """
    
    def __init__(self):
        self.nsfw_lexicon = self._load_nsfw_lexicon()
        self.spam_patterns = self._load_spam_patterns()
        self.hate_speech_lexicon = self._load_hate_speech_lexicon()
        self.quality_rules = self._load_quality_rules()
        self.moderation_policies = self._load_moderation_policies()
        self.user_profiles = {}
        
        logger.info("Content Moderator initialized")

    def _load_nsfw_lexicon(self) -> Dict[str, float]:
        """Load NSFW content detection lexicon."""
        return {
            # Explicit content
            "porn": 0.9, "sex": 0.8, "nude": 0.9, "xxx": 0.9,
            "adult": 0.7, "erotic": 0.8, "sexual": 0.8,
            
            # Violence and gore
            "kill": 0.6, "murder": 0.9, "violence": 0.8, "gore": 0.9,
            "blood": 0.7, "weapon": 0.6, "gun": 0.7, "knife": 0.7,
            
            # Substance abuse
            "drug": 0.8, "cocaine": 0.9, "heroin": 0.9, "meth": 0.9,
            "alcohol": 0.5, "weed": 0.7, "marijuana": 0.8,
            
            # Self-harm
            "suicide": 0.9, "selfharm": 0.9, "cutting": 0.8, "die": 0.7
        }

    def _load_spam_patterns(self) -> List[Dict[str, Any]]:
        """Load spam detection patterns."""
        return [
            {
                "pattern": r"(?i)(?:buy|sell|cheap|free|win|prize|money|earn|$$$)",
                "weight": 0.3,
                "description": "Commercial spam keywords"
            },
            {
                "pattern": r"(?:http[s]?://|www\.)\S{20,}",
                "weight": 0.4,
                "description": "Excessive URL length"
            },
            {
                "pattern": r"(.)\1{3,}",
                "weight": 0.2,
                "description": "Excessive character repetition"
            },
            {
                "pattern": r"(?i)(?:click|link|visit|download|install)",
                "weight": 0.2,
                "description": "Clickbait language"
            },
            {
                "pattern": r"[A-Z]{10,}",
                "weight": 0.3,
                "description": "Excessive capitalization"
            }
        ]

    def _load_hate_speech_lexicon(self) -> Dict[str, float]:
        """Load hate speech detection lexicon."""
        return {
            # Racial slurs
            "nigger": 1.0, "nigga": 0.9, "chink": 0.9, "spic": 0.9,
            "wetback": 0.9, "kike": 0.9, "gook": 0.9, "coon": 0.9,
            
            # Religious hate
            "jew": 0.6, "muslim": 0.6, "christian": 0.6, "islam": 0.7,
            "terrorist": 0.8, "infidel": 0.8, "heretic": 0.7,
            
            # Gender/sexual orientation hate
            "fag": 0.9, "faggot": 0.9, "dyke": 0.8, "tranny": 0.8,
            "slut": 0.7, "whore": 0.8, "bitch": 0.6,
            
            # General hate
            "hate": 0.7, "kill": 0.6, "death": 0.6, "destroy": 0.7,
            "eliminate": 0.8, "exterminate": 0.9
        }

    def _load_quality_rules(self) -> Dict[str, Any]:
        """Load content quality assessment rules."""
        return {
            "minimum_length": 10,
            "maximum_length": 5000,
            "max_consecutive_chars": 5,
            "max_consecutive_words": 3,
            "allowed_languages": ["en", "es", "fr", "de", "it", "pt"],
            "forbidden_patterns": [
                r"^\s*$",  # Empty content
                r"^[^\w\s]+$",  # Only symbols
                r"^\d{10,}$"  # Only numbers
            ]
        }

    def _load_moderation_policies(self) -> Dict[str, Any]:
        """Load moderation policies and thresholds."""
        return {
            "nsfw_threshold": 0.7,
            "spam_threshold": 0.6,
            "hate_speech_threshold": 0.5,
            "quality_threshold": 0.3,
            "combined_threshold": 0.8,
            "user_trust_boost": 0.1,  # Reduce scores for trusted users
            "user_penalty": 0.2      # Increase scores for problematic users
        }

    async def moderate_content(self, content: Dict[str, Any]) -> ModerationResult:
        """
        Moderate a piece of content.
        
        Args:
            content: Content to moderate with structure:
                    {
                        "id": str,
                        "text": str,
                        "author_id": str,
                        "timestamp": datetime,
                        "metadata": Dict
                    }
        
        Returns:
            ModerationResult with moderation decision
        """
        try:
            content_id = content.get("id", "")
            text = content.get("text", "")
            author_id = content.get("author_id", "")
            content_type = content.get("content_type", "text")
            
            if not text.strip():
                return ModerationResult(
                    content_id=content_id,
                    content_type=content_type,
                    moderation_score=0.0,
                    moderation_level="allow",
                    detected_issues=[],
                    confidence=1.0,
                    suggested_action="allow",
                    metadata={"reason": "empty_content"}
                )
            
            # Get user profile
            user_profile = self._get_user_profile(author_id)
            
            # Analyze content
            nsfw_score = self._analyze_nsfw_content(text)
            spam_score = self._analyze_spam_content(text)
            hate_score = self._analyze_hate_speech(text)
            quality_score = self._analyze_content_quality(text)
            
            # Calculate combined score
            combined_score = self._calculate_combined_score(
                nsfw_score, spam_score, hate_score, quality_score, user_profile
            )
            
            # Determine moderation level
            moderation_level = self._determine_moderation_level(combined_score)
            
            # Generate detected issues
            detected_issues = self._generate_detected_issues(
                nsfw_score, spam_score, hate_score, quality_score
            )
            
            # Determine suggested action
            suggested_action = self._determine_suggested_action(
                moderation_level, detected_issues
            )
            
            # Calculate confidence
            confidence = self._calculate_moderation_confidence(
                nsfw_score, spam_score, hate_score, quality_score
            )
            
            # Update user profile
            await self._update_user_profile(author_id, moderation_level, detected_issues)
            
            return ModerationResult(
                content_id=content_id,
                content_type=content_type,
                moderation_score=combined_score,
                moderation_level=moderation_level,
                detected_issues=detected_issues,
                confidence=confidence,
                suggested_action=suggested_action,
                metadata={
                    "nsfw_score": nsfw_score,
                    "spam_score": spam_score,
                    "hate_score": hate_score,
                    "quality_score": quality_score,
                    "user_trust_score": user_profile.trust_score if user_profile else 0.5
                }
            )
            
        except Exception as e:
            logger.error(f"Error moderating content {content.get('id', 'unknown')}: {e}")
            return ModerationResult(
                content_id=content.get("id", ""),
                content_type=content.get("content_type", "text"),
                moderation_score=1.0,
                moderation_level="block",
                detected_issues=["moderation_error"],
                confidence=0.0,
                suggested_action="manual_review",
                metadata={"error": str(e)}
            )

    async def moderate_batch(self, content_batch: List[Dict[str, Any]]) -> List[ModerationResult]:
        """
        Moderate a batch of content items.
        
        Args:
            content_batch: List of content items to moderate
            
        Returns:
            List of ModerationResults
        """
        try:
            moderation_results = []
            
            for content in content_batch:
                result = await self.moderate_content(content)
                moderation_results.append(result)
            
            return moderation_results
            
        except Exception as e:
            logger.error(f"Error moderating batch: {e}")
            return []

    async def update_user_moderation_profile(self, user_id: str, 
                                           violation_type: str, 
                                           severity: float) -> UserModerationProfile:
        """
        Update user moderation profile based on violation.
        
        Args:
            user_id: User identifier
            violation_type: Type of violation
            severity: Severity of violation (0.0 to 1.0)
            
        Returns:
            Updated UserModerationProfile
        """
        try:
            profile = self._get_user_profile(user_id)
            
            # Add violation to history
            violation = {
                "type": violation_type,
                "severity": severity,
                "timestamp": datetime.now(),
                "action": "violation_recorded"
            }
            
            profile.violation_history.append(violation)
            profile.moderation_count += 1
            
            # Update trust score
            trust_penalty = severity * 0.1
            profile.trust_score = max(0.0, profile.trust_score - trust_penalty)
            
            # Update risk level
            profile.risk_level = self._calculate_risk_level(profile)
            
            # Update last moderation action
            profile.last_moderation_action = f"violation_{violation_type}"
            
            return profile
            
        except Exception as e:
            logger.error(f"Error updating user profile for {user_id}: {e}")
            return self._get_user_profile(user_id)

    def get_user_moderation_profile(self, user_id: str) -> Optional[UserModerationProfile]:
        """Get user moderation profile."""
        return self.user_profiles.get(user_id)

    def set_moderation_policy(self, policy_name: str, value: Any):
        """Update moderation policy."""
        if policy_name in self.moderation_policies:
            self.moderation_policies[policy_name] = value
            logger.info(f"Updated moderation policy: {policy_name} = {value}")

    # Private helper methods
    
    def _get_user_profile(self, user_id: str) -> UserModerationProfile:
        """Get or create user moderation profile."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserModerationProfile(
                user_id=user_id,
                violation_history=[],
                trust_score=1.0,  # Start with maximum trust
                risk_level="low",
                last_moderation_action=None,
                moderation_count=0
            )
        
        return self.user_profiles[user_id]

    def _analyze_nsfw_content(self, text: str) -> float:
        """Analyze content for NSFW elements."""
        text_lower = text.lower()
        nsfw_score = 0.0
        
        for word, weight in self.nsfw_lexicon.items():
            if word in text_lower:
                nsfw_score = max(nsfw_score, weight)
        
        # Check for encoded/obfuscated content
        if self._contains_obfuscated_nsfw(text):
            nsfw_score = max(nsfw_score, 0.8)
        
        return nsfw_score

    def _analyze_spam_content(self, text: str) -> float:
        """Analyze content for spam elements."""
        spam_score = 0.0
        
        for pattern_config in self.spam_patterns:
            pattern = pattern_config["pattern"]
            weight = pattern_config["weight"]
            
            if re.search(pattern, text):
                spam_score += weight
        
        # Normalize spam score
        spam_score = min(spam_score, 1.0)
        
        # Check for excessive repetition
        repetition_score = self._calculate_repetition_score(text)
        spam_score = max(spam_score, repetition_score)
        
        return spam_score

    def _analyze_hate_speech(self, text: str) -> float:
        """Analyze content for hate speech elements."""
        text_lower = text.lower()
        hate_score = 0.0
        
        for word, weight in self.hate_speech_lexicon.items():
            if word in text_lower:
                hate_score = max(hate_score, weight)
        
        # Check for hate speech patterns
        if self._contains_hate_patterns(text):
            hate_score = max(hate_score, 0.7)
        
        return hate_score

    def _analyze_content_quality(self, text: str) -> float:
        """Analyze content quality."""
        quality_issues = 0.0
        
        # Check length
        if len(text) < self.quality_rules["minimum_length"]:
            quality_issues += 0.3
        elif len(text) > self.quality_rules["maximum_length"]:
            quality_issues += 0.2
        
        # Check for forbidden patterns
        for pattern in self.quality_rules["forbidden_patterns"]:
            if re.match(pattern, text):
                quality_issues += 0.5
                break
        
        # Check character repetition
        if self._has_excessive_repetition(text):
            quality_issues += 0.3
        
        # Check language quality (simplified)
        if self._is_low_quality_language(text):
            quality_issues += 0.2
        
        return min(quality_issues, 1.0)

    def _calculate_combined_score(self, nsfw_score: float, spam_score: float,
                                hate_score: float, quality_score: float,
                                user_profile: UserModerationProfile) -> float:
        """Calculate combined moderation score."""
        # Base scores with weights
        weights = {
            "nsfw": 0.3,
            "spam": 0.2,
            "hate": 0.4,
            "quality": 0.1
        }
        
        base_score = (
            nsfw_score * weights["nsfw"] +
            spam_score * weights["spam"] +
            hate_score * weights["hate"] +
            quality_score * weights["quality"]
        )
        
        # Apply user trust adjustment
        if user_profile:
            trust_adjustment = (1.0 - user_profile.trust_score) * self.moderation_policies["user_penalty"]
            base_score += trust_adjustment
        
        return min(base_score, 1.0)

    def _determine_moderation_level(self, combined_score: float) -> str:
        """Determine moderation level based on score."""
        if combined_score >= self.moderation_policies["combined_threshold"]:
            return "block"
        elif combined_score >= self.moderation_policies["spam_threshold"]:
            return "flag"
        else:
            return "allow"

    def _generate_detected_issues(self, nsfw_score: float, spam_score: float,
                                hate_score: float, quality_score: float) -> List[str]:
        """Generate list of detected issues."""
        issues = []
        
        if nsfw_score >= self.moderation_policies["nsfw_threshold"]:
            issues.append("nsfw_content")
        
        if spam_score >= self.moderation_policies["spam_threshold"]:
            issues.append("spam_content")
        
        if hate_score >= self.moderation_policies["hate_speech_threshold"]:
            issues.append("hate_speech")
        
        if quality_score >= self.moderation_policies["quality_threshold"]:
            issues.append("low_quality")
        
        return issues

    def _determine_suggested_action(self, moderation_level: str, 
                                  detected_issues: List[str]) -> str:
        """Determine suggested moderation action."""
        if moderation_level == "block":
            return "remove_content"
        elif moderation_level == "flag":
            return "manual_review"
        else:
            return "allow_content"

    def _calculate_moderation_confidence(self, nsfw_score: float, spam_score: float,
                                       hate_score: float, quality_score: float) -> float:
        """Calculate confidence in moderation decision."""
        # Higher confidence for extreme scores
        max_score = max(nsfw_score, spam_score, hate_score, quality_score)
        
        if max_score > 0.8:
            return 0.9
        elif max_score > 0.5:
            return 0.7
        elif max_score > 0.3:
            return 0.5
        else:
            return 0.3

    async def _update_user_profile(self, user_id: str, moderation_level: str,
                                 detected_issues: List[str]):
        """Update user moderation profile."""
        profile = self._get_user_profile(user_id)
        
        # Record moderation action
        if moderation_level != "allow":
            violation_type = detected_issues[0] if detected_issues else "general"
            severity = 0.5 if moderation_level == "flag" else 1.0
            
            await self.update_user_moderation_profile(user_id, violation_type, severity)

    def _contains_obfuscated_nsfw(self, text: str) -> bool:
        """Check for obfuscated NSFW content."""
        # Check for leetspeak and character substitution
        obfuscated_patterns = [
            r"[n!][1i!][g@][g6][3e!]",  # nigge
            r"[p@][0o][r!n]",          # porn
            r"[s3$][3e!][x]",          # sex
        ]
        
        for pattern in obfuscated_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

    def _contains_hate_patterns(self, text: str) -> bool:
        """Check for hate speech patterns."""
        hate_patterns = [
            r"(?i)\bkill.*\b",     # Kill threats
            r"(?i)\bdeath.*\b",    # Death threats
            r"(?i)\bdestroy.*\b",  # Destruction
        ]
        
        for pattern in hate_patterns:
            if re.search(pattern, text):
                return True
        
        return False

    def _calculate_repetition_score(self, text: str) -> float:
        """Calculate score based on content repetition."""
        words = text.lower().split()
        
        if len(words) < 5:
            return 0.0
        
        # Check for repeated phrases
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        max_repetition = max(word_counts.values()) if word_counts else 0
        repetition_ratio = max_repetition / len(words)
        
        if repetition_ratio > 0.3:  # More than 30% repetition
            return 0.6
        elif repetition_ratio > 0.2:
            return 0.4
        else:
            return 0.0

    def _has_excessive_repetition(self, text: str) -> bool:
        """Check for excessive character or word repetition."""
        # Check character repetition
        if re.search(r'(.)\1{5,}', text):
            return True
        
        # Check word repetition
        words = text.lower().split()
        for i in range(len(words) - 2):
            if words[i] == words[i+1] == words[i+2]:
                return True
        
        return False

    def _is_low_quality_language(self, text: str) -> bool:
        """Check if content has low language quality."""
        # Check for excessive symbols
        symbol_ratio = len(re.findall(r'[^\w\s]', text)) / len(text) if text else 0
        if symbol_ratio > 0.3:
            return True
        
        # Check for excessive numbers
        number_ratio = len(re.findall(r'\d', text)) / len(text) if text else 0
        if number_ratio > 0.4:
            return True
        
        # Check for very short words only
        words = text.split()
        if words:
            short_word_ratio = len([w for w in words if len(w) <= 2]) / len(words)
            if short_word_ratio > 0.7:
                return True
        
        return False

    def _calculate_risk_level(self, profile: UserModerationProfile) -> str:
        """Calculate user risk level based on history."""
        if not profile.violation_history:
            return "low"
        
        # Calculate average severity
        total_severity = sum(v["severity"] for v in profile.violation_history)
        avg_severity = total_severity / len(profile.violation_history)
        
        # Calculate recent violations (last 30 days)
        recent_violations = [
            v for v in profile.violation_history
            if (datetime.now() - v["timestamp"]).days <= 30
        ]
        
        if avg_severity > 0.7 or len(recent_violations) > 5:
            return "high"
        elif avg_severity > 0.4 or len(recent_violations) > 2:
            return "medium"
        else:
            return "low"

    def _normalize_text(self, text: str) -> str:
        """Normalize text for analysis."""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Remove zero-width characters
        text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
        
        return text

    def _check_language_quality(self, text: str) -> float:
        """Check language quality and coherence."""
        # Simple language detection (would use proper library in production)
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        total_words = len(text.split())
        
        if total_words == 0:
            return 0.0
        
        english_ratio = english_words / total_words
        
        # Penalize non-English content if policy requires
        if english_ratio < 0.5:
            return 0.3
        
        return 0.0

    def _analyze_sentiment_extremes(self, text: str) -> float:
        """Analyze for extreme sentiment that might indicate problematic content."""
        # Simple sentiment analysis (would use proper model in production)
        negative_words = ['hate', 'kill', 'die', 'death', 'destroy', 'bad', 'terrible']
        positive_words = ['love', 'great', 'amazing', 'wonderful', 'best']
        
        text_lower = text.lower()
        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)
        
        # Check for extreme negativity
        if negative_count > 3:
            return 0.6
        
        # Check for extreme positivity (possible spam)
        if positive_count > 5:
            return 0.4
        
        return 0.0

    def _check_for_automated_behavior(self, user_id: str, content: str) -> float:
        """Check for signs of automated/robotic behavior."""
        profile = self._get_user_profile(user_id)
        
        # Check posting frequency (simplified)
        recent_posts = len([
            v for v in profile.violation_history
            if (datetime.now() - v["timestamp"]).seconds < 3600  # Last hour
        ])
        
        if recent_posts > 10:  # More than 10 posts in an hour
            return 0.5
        
        return 0.0

    def _analyze_content_context(self, text: str, context: Dict[str, Any]) -> float:
        """Analyze content in context of surrounding information."""
        context_score = 0.0
        
        # Check time-based patterns
        if "timestamp" in context:
            hour = context["timestamp"].hour
            if hour < 6 or hour > 23:  # Late night/early morning
                context_score += 0.1
        
        # Check platform-specific patterns
        if "platform" in context:
            platform = context["platform"]
            if platform in ["anonymous", "unmoderated"]:
                context_score += 0.2
        
        return context_score

    def _generate_moderation_report(self, results: List[ModerationResult]) -> Dict[str, Any]:
        """Generate moderation report for a batch of content."""
        total_content = len(results)
        blocked_count = len([r for r in results if r.moderation_level == "block"])
        flagged_count = len([r for r in results if r.moderation_level == "flag"])
        allowed_count = len([r for r in results if r.moderation_level == "allow"])
        
        # Analyze issue distribution
        issue_counts = {}
        for result in results:
            for issue in result.detected_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        return {
            "total_content": total_content,
            "blocked_count": blocked_count,
            "flagged_count": flagged_count,
            "allowed_count": allowed_count,
            "block_rate": blocked_count / total_content if total_content > 0 else 0,
            "flag_rate": flagged_count / total_content if total_content > 0 else 0,
            "issue_distribution": issue_counts,
            "average_confidence": sum(r.confidence for r in results) / len(results) if results else 0,
            "report_generated": datetime.now().isoformat()
        }