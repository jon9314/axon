"""Natural-language date parsing for reminders.

This module provides parsing of human-readable date expressions like:
- "tomorrow at 3pm"
- "next Friday"
- "in 2 hours"
- "December 25th"
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

try:
    from datetime import UTC
except ImportError:
    # Python < 3.11
    import datetime as dt

    UTC = dt.UTC  # type: ignore


class DateParseResult:
    """Result of parsing a natural language date expression."""

    def __init__(
        self,
        timestamp: int,
        datetime_obj: datetime,
        original_text: str,
        confidence: float = 1.0,
        components: dict | None = None,
    ) -> None:
        self.timestamp = timestamp
        self.datetime_obj = datetime_obj
        self.original_text = original_text
        self.confidence = confidence
        self.components = components or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "datetime": self.datetime_obj.isoformat(),
            "original_text": self.original_text,
            "confidence": self.confidence,
            "components": self.components,
        }


class NaturalDateParser:
    """Parse natural language date expressions into timestamps."""

    def __init__(self, base_time: datetime | None = None) -> None:
        """Initialize parser.

        Args:
            base_time: Reference time for relative dates (defaults to now)
        """
        self.base_time = base_time or datetime.now(UTC)

    def parse(self, text: str) -> DateParseResult | None:
        """Parse natural language date expression.

        Args:
            text: Natural language date expression

        Returns:
            DateParseResult if parsing successful, None otherwise

        Examples:
            >>> parser = NaturalDateParser()
            >>> result = parser.parse("tomorrow at 3pm")
            >>> result = parser.parse("in 2 hours")
            >>> result = parser.parse("next Friday")
        """
        text = text.lower().strip()

        # Try different parsing strategies in order of specificity
        parsers = [
            self._parse_relative_time,
            self._parse_named_day,
            self._parse_time_today,
            self._parse_absolute_date,
            self._parse_weekday,
        ]

        for parser_func in parsers:
            result = parser_func(text)
            if result:
                return result

        return None

    def _parse_relative_time(self, text: str) -> DateParseResult | None:
        """Parse relative time expressions like 'in 2 hours', 'in 30 minutes'."""
        # Pattern: "in X hours/minutes/days/weeks"
        patterns = [
            (r"in (\d+) hours?", "hours"),
            (r"in (\d+) minutes?", "minutes"),
            (r"in (\d+) days?", "days"),
            (r"in (\d+) weeks?", "weeks"),
            (r"in (\d+) seconds?", "seconds"),
        ]

        for pattern, unit in patterns:
            match = re.search(pattern, text)
            if match:
                value = int(match.group(1))
                delta_kwargs = {unit: value}
                target_time = self.base_time + timedelta(**delta_kwargs)

                return DateParseResult(
                    timestamp=int(target_time.timestamp()),
                    datetime_obj=target_time,
                    original_text=text,
                    confidence=0.95,
                    components={"type": "relative", "unit": unit, "value": value},
                )

        return None

    def _parse_named_day(self, text: str) -> DateParseResult | None:
        """Parse named days like 'tomorrow', 'today', 'yesterday'."""
        # Handle time component if present
        time_match = re.search(r"at (\d{1,2}):?(\d{2})?\s*(am|pm)?", text)
        hour = 0
        minute = 0

        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            am_pm = time_match.group(3)

            if am_pm == "pm" and hour < 12:
                hour += 12
            elif am_pm == "am" and hour == 12:
                hour = 0

        # Named days
        if "tomorrow" in text:
            target_date = (self.base_time + timedelta(days=1)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            return DateParseResult(
                timestamp=int(target_date.timestamp()),
                datetime_obj=target_date,
                original_text=text,
                confidence=0.95,
                components={"type": "named_day", "day": "tomorrow", "hour": hour, "minute": minute},
            )

        if "today" in text:
            target_date = self.base_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return DateParseResult(
                timestamp=int(target_date.timestamp()),
                datetime_obj=target_date,
                original_text=text,
                confidence=0.95,
                components={"type": "named_day", "day": "today", "hour": hour, "minute": minute},
            )

        if "yesterday" in text:
            target_date = (self.base_time - timedelta(days=1)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            return DateParseResult(
                timestamp=int(target_date.timestamp()),
                datetime_obj=target_date,
                original_text=text,
                confidence=0.95,
                components={"type": "named_day", "day": "yesterday", "hour": hour, "minute": minute},
            )

        # Handle "tonight" specifically (assume 8 PM if no time given)
        if "tonight" in text:
            hour = hour if time_match else 20
            target_date = self.base_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return DateParseResult(
                timestamp=int(target_date.timestamp()),
                datetime_obj=target_date,
                original_text=text,
                confidence=0.90,
                components={"type": "named_day", "day": "tonight", "hour": hour, "minute": minute},
            )

        return None

    def _parse_time_today(self, text: str) -> DateParseResult | None:
        """Parse time expressions like '3pm', '14:30', '9:00 AM'."""
        # Pattern: "HH:MM AM/PM" or "H AM/PM"
        patterns = [
            r"(\d{1,2}):(\d{2})\s*(am|pm)?",
            r"(\d{1,2})\s*(am|pm)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if len(match.groups()) > 2 and match.group(2) else 0
                am_pm = match.group(3) if len(match.groups()) > 2 else match.group(2)

                if am_pm:
                    if am_pm.lower() == "pm" and hour < 12:
                        hour += 12
                    elif am_pm.lower() == "am" and hour == 12:
                        hour = 0

                target_time = self.base_time.replace(hour=hour, minute=minute, second=0, microsecond=0)

                # If the time has already passed today, assume tomorrow
                if target_time < self.base_time:
                    target_time += timedelta(days=1)

                return DateParseResult(
                    timestamp=int(target_time.timestamp()),
                    datetime_obj=target_time,
                    original_text=text,
                    confidence=0.85,
                    components={"type": "time_today", "hour": hour, "minute": minute},
                )

        return None

    def _parse_weekday(self, text: str) -> DateParseResult | None:
        """Parse weekday expressions like 'next Monday', 'this Friday'."""
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        # Extract time if present
        time_match = re.search(r"at (\d{1,2}):?(\d{2})?\s*(am|pm)?", text)
        hour = 9  # Default to 9 AM
        minute = 0

        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            am_pm = time_match.group(3)

            if am_pm and am_pm.lower() == "pm" and hour < 12:
                hour += 12
            elif am_pm and am_pm.lower() == "am" and hour == 12:
                hour = 0

        for day_name, day_num in weekdays.items():
            if day_name in text:
                current_weekday = self.base_time.weekday()
                days_ahead = day_num - current_weekday

                # Determine if it's "next" or "this" week
                if "next" in text:
                    if days_ahead <= 0:
                        days_ahead += 7
                else:  # "this" or just the day name
                    if days_ahead < 0:
                        days_ahead += 7

                target_date = (self.base_time + timedelta(days=days_ahead)).replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

                return DateParseResult(
                    timestamp=int(target_date.timestamp()),
                    datetime_obj=target_date,
                    original_text=text,
                    confidence=0.85,
                    components={
                        "type": "weekday",
                        "day_name": day_name,
                        "days_ahead": days_ahead,
                        "hour": hour,
                        "minute": minute,
                    },
                )

        return None

    def _parse_absolute_date(self, text: str) -> DateParseResult | None:
        """Parse absolute dates like 'December 25', '2024-12-25'."""
        # Pattern: "Month Day" or "Month Day, Year"
        months = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }

        for month_name, month_num in months.items():
            # Match "Month Day" or "Month Day, Year"
            pattern = rf"{month_name}\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s*(\d{{4}})?"
            match = re.search(pattern, text)

            if match:
                day = int(match.group(1))
                year = int(match.group(2)) if match.group(2) else self.base_time.year

                # Extract time if present
                time_match = re.search(r"at (\d{1,2}):?(\d{2})?\s*(am|pm)?", text)
                hour = 9
                minute = 0

                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    am_pm = time_match.group(3)

                    if am_pm and am_pm.lower() == "pm" and hour < 12:
                        hour += 12
                    elif am_pm and am_pm.lower() == "am" and hour == 12:
                        hour = 0

                try:
                    target_date = datetime(year, month_num, day, hour, minute, 0, tzinfo=UTC)

                    return DateParseResult(
                        timestamp=int(target_date.timestamp()),
                        datetime_obj=target_date,
                        original_text=text,
                        confidence=0.90,
                        components={
                            "type": "absolute",
                            "year": year,
                            "month": month_num,
                            "day": day,
                            "hour": hour,
                            "minute": minute,
                        },
                    )
                except ValueError:
                    # Invalid date
                    continue

        # Try ISO format
        iso_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
        if iso_match:
            year = int(iso_match.group(1))
            month = int(iso_match.group(2))
            day = int(iso_match.group(3))

            try:
                target_date = datetime(year, month, day, 9, 0, 0, tzinfo=UTC)

                return DateParseResult(
                    timestamp=int(target_date.timestamp()),
                    datetime_obj=target_date,
                    original_text=text,
                    confidence=0.95,
                    components={
                        "type": "iso_date",
                        "year": year,
                        "month": month,
                        "day": day,
                    },
                )
            except ValueError:
                pass

        return None

    def parse_duration(self, text: str) -> int | None:
        """Parse duration expressions into seconds.

        Args:
            text: Duration expression (e.g., "2 hours", "30 minutes")

        Returns:
            Duration in seconds, or None if parsing failed
        """
        patterns = [
            (r"(\d+)\s*hours?", 3600),
            (r"(\d+)\s*minutes?", 60),
            (r"(\d+)\s*seconds?", 1),
            (r"(\d+)\s*days?", 86400),
            (r"(\d+)\s*weeks?", 604800),
        ]

        total_seconds = 0

        for pattern, multiplier in patterns:
            match = re.search(pattern, text.lower())
            if match:
                value = int(match.group(1))
                total_seconds += value * multiplier

        return total_seconds if total_seconds > 0 else None
