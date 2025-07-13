from tools import select_tool, CreateEventTool, ListEventsTool


def test_select_create_event() -> None:
    tool = select_tool("please book a meeting tomorrow")
    assert isinstance(tool, CreateEventTool)


def test_select_check_availability() -> None:
    tool = select_tool("am I free on friday?")
    assert isinstance(tool, ListEventsTool)
