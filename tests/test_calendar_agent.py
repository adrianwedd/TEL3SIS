from agents.calendar_agent import CalendarAgent


def test_detect_create_event() -> None:
    agent = CalendarAgent()
    intent = agent.detect_intent("please book a meeting tomorrow")
    assert intent == "create_event"


def test_detect_check_availability() -> None:
    agent = CalendarAgent()
    intent = agent.detect_intent("am I free on Friday?")
    assert intent == "check_availability"
