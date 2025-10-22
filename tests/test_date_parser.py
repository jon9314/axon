"""Tests for natural language date parser."""

from datetime import datetime, timedelta

import pytest

from agent.date_parser import NaturalDateParser

try:
    from datetime import UTC
except ImportError:
    import datetime as dt

    UTC = dt.UTC


@pytest.fixture
def parser():
    """Date parser with fixed base time."""
    # Fixed base time: 2025-01-15 10:00:00 UTC (Wednesday)
    base_time = datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC)
    return NaturalDateParser(base_time=base_time)


class TestRelativeTime:
    """Tests for relative time expressions."""

    def test_parse_in_hours(self, parser):
        """Should parse 'in X hours'."""
        result = parser.parse("in 2 hours")

        assert result is not None
        assert result.components["type"] == "relative"
        assert result.components["unit"] == "hours"
        assert result.components["value"] == 2
        assert result.confidence == 0.95

    def test_parse_in_minutes(self, parser):
        """Should parse 'in X minutes'."""
        result = parser.parse("in 30 minutes")

        assert result is not None
        assert result.components["unit"] == "minutes"
        assert result.components["value"] == 30

    def test_parse_in_days(self, parser):
        """Should parse 'in X days'."""
        result = parser.parse("in 5 days")

        assert result is not None
        assert result.components["unit"] == "days"
        assert result.components["value"] == 5

    def test_parse_in_weeks(self, parser):
        """Should parse 'in X weeks'."""
        result = parser.parse("in 2 weeks")

        assert result is not None
        assert result.components["unit"] == "weeks"
        assert result.components["value"] == 2


class TestNamedDays:
    """Tests for named day expressions."""

    def test_parse_tomorrow(self, parser):
        """Should parse 'tomorrow'."""
        result = parser.parse("tomorrow")

        assert result is not None
        assert result.components["type"] == "named_day"
        assert result.components["day"] == "tomorrow"
        # Should be same time next day
        expected = parser.base_time + timedelta(days=1)
        assert result.datetime_obj.date() == expected.date()

    def test_parse_tomorrow_with_time(self, parser):
        """Should parse 'tomorrow at 3pm'."""
        result = parser.parse("tomorrow at 3pm")

        assert result is not None
        assert result.components["day"] == "tomorrow"
        assert result.components["hour"] == 15
        assert result.components["minute"] == 0

    def test_parse_today(self, parser):
        """Should parse 'today'."""
        result = parser.parse("today")

        assert result is not None
        assert result.components["day"] == "today"
        assert result.datetime_obj.date() == parser.base_time.date()

    def test_parse_today_with_time(self, parser):
        """Should parse 'today at 5:30pm'."""
        result = parser.parse("today at 5:30pm")

        assert result is not None
        assert result.components["hour"] == 17
        assert result.components["minute"] == 30

    def test_parse_tonight(self, parser):
        """Should parse 'tonight' (default 8 PM)."""
        result = parser.parse("tonight")

        assert result is not None
        assert result.components["day"] == "tonight"
        assert result.components["hour"] == 20  # Default to 8 PM


class TestTimeToday:
    """Tests for time expressions."""

    def test_parse_time_24hour(self, parser):
        """Should parse 24-hour time."""
        result = parser.parse("14:30")

        assert result is not None
        assert result.components["type"] == "time_today"
        assert result.components["hour"] == 14
        assert result.components["minute"] == 30

    def test_parse_time_12hour_pm(self, parser):
        """Should parse 12-hour time PM."""
        result = parser.parse("3pm")

        assert result is not None
        assert result.components["hour"] == 15

    def test_parse_time_12hour_am(self, parser):
        """Should parse 12-hour time AM."""
        result = parser.parse("9am")

        assert result is not None
        assert result.components["hour"] == 9

    def test_parse_time_with_colon_and_ampm(self, parser):
        """Should parse time with colon and AM/PM."""
        result = parser.parse("2:45 PM")

        assert result is not None
        assert result.components["hour"] == 14
        assert result.components["minute"] == 45


class TestWeekdays:
    """Tests for weekday expressions."""

    def test_parse_next_monday(self, parser):
        """Should parse 'next Monday'."""
        result = parser.parse("next Monday")

        assert result is not None
        assert result.components["type"] == "weekday"
        assert result.components["day_name"] == "monday"
        # Base time is Wednesday (2025-01-15), next Monday is 2025-01-20
        assert result.datetime_obj.weekday() == 0  # Monday

    def test_parse_friday(self, parser):
        """Should parse 'Friday' (this week or next)."""
        result = parser.parse("Friday")

        assert result is not None
        assert result.components["day_name"] == "friday"
        assert result.datetime_obj.weekday() == 4  # Friday

    def test_parse_weekday_with_time(self, parser):
        """Should parse 'Monday at 9am'."""
        result = parser.parse("Monday at 9am")

        assert result is not None
        assert result.components["hour"] == 9
        assert result.components["minute"] == 0


class TestAbsoluteDates:
    """Tests for absolute date expressions."""

    def test_parse_month_day(self, parser):
        """Should parse 'December 25'."""
        result = parser.parse("December 25")

        assert result is not None
        assert result.components["type"] == "absolute"
        assert result.components["month"] == 12
        assert result.components["day"] == 25

    def test_parse_month_day_with_suffix(self, parser):
        """Should parse 'January 1st'."""
        result = parser.parse("January 1st")

        assert result is not None
        assert result.components["month"] == 1
        assert result.components["day"] == 1

    def test_parse_month_day_year(self, parser):
        """Should parse 'March 15, 2026'."""
        result = parser.parse("March 15, 2026")

        assert result is not None
        assert result.components["year"] == 2026
        assert result.components["month"] == 3
        assert result.components["day"] == 15

    def test_parse_abbreviated_month(self, parser):
        """Should parse abbreviated month names."""
        result = parser.parse("Feb 14")

        assert result is not None
        assert result.components["month"] == 2
        assert result.components["day"] == 14

    def test_parse_iso_date(self, parser):
        """Should parse ISO date format."""
        result = parser.parse("2025-06-01")

        assert result is not None
        assert result.components["type"] == "iso_date"
        assert result.components["year"] == 2025
        assert result.components["month"] == 6
        assert result.components["day"] == 1


class TestDuration:
    """Tests for duration parsing."""

    def test_parse_duration_hours(self, parser):
        """Should parse duration in hours."""
        seconds = parser.parse_duration("2 hours")

        assert seconds == 7200  # 2 * 3600

    def test_parse_duration_minutes(self, parser):
        """Should parse duration in minutes."""
        seconds = parser.parse_duration("30 minutes")

        assert seconds == 1800  # 30 * 60

    def test_parse_duration_days(self, parser):
        """Should parse duration in days."""
        seconds = parser.parse_duration("1 day")

        assert seconds == 86400  # 24 * 3600

    def test_parse_duration_combined(self, parser):
        """Should parse combined duration."""
        seconds = parser.parse_duration("2 hours and 30 minutes")

        assert seconds == 9000  # 2*3600 + 30*60

    def test_parse_duration_invalid(self, parser):
        """Should return None for invalid duration."""
        seconds = parser.parse_duration("invalid")

        assert seconds is None


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_empty_string(self, parser):
        """Should return None for empty string."""
        result = parser.parse("")

        assert result is None

    def test_parse_invalid_expression(self, parser):
        """Should return None for invalid expression."""
        result = parser.parse("not a date")

        assert result is None

    def test_parse_case_insensitive(self, parser):
        """Should be case insensitive."""
        result1 = parser.parse("TOMORROW")
        result2 = parser.parse("tomorrow")

        assert result1 is not None
        assert result2 is not None
        assert result1.timestamp == result2.timestamp


class TestDateParseResult:
    """Tests for DateParseResult class."""

    def test_to_dict(self, parser):
        """Should convert result to dictionary."""
        result = parser.parse("tomorrow at 3pm")

        data = result.to_dict()

        assert "timestamp" in data
        assert "datetime" in data
        assert "original_text" in data
        assert "confidence" in data
        assert "components" in data
        assert data["original_text"] == "tomorrow at 3pm"
