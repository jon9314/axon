from agent.calendar_exporter import CalendarExporter


class DummyMem:
    def list_facts(self, thread_id: str, tag: str | None = None):
        return [
            (
                "reminder_1",
                '{"message": "Meet", "time": 1609459200}',
                None,
                False,
                [],
            )
        ]


def test_export(tmp_path):
    exporter = CalendarExporter(DummyMem())
    data = exporter.export("t1")
    assert "BEGIN:VCALENDAR" in data
    assert "Meet" in data
    file_path = tmp_path / "events.ics"
    exporter.export("t1", path=str(file_path))
    assert file_path.read_text("utf-8").startswith("BEGIN:VCALENDAR")
