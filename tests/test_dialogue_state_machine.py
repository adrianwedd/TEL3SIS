from agents.dialog_state_machine import DialogueStateMachine


def test_dialog_flow() -> None:
    machine = DialogueStateMachine()
    assert machine.next_prompt() == "What is the event title?"

    p = machine.handle_input("Team meeting")
    assert p == "What date is the event?"
    assert machine.data["title"] == "Team meeting"

    p = machine.handle_input("Next Friday")
    assert p == "What time does it start?"
    assert machine.data["date"] == "Next Friday"

    p = machine.handle_input("2pm")
    assert "correct?" in p
    assert machine.data["time"] == "2pm"

    p = machine.handle_input("yes")
    assert p == "Thank you."
    assert machine.is_complete()
    assert machine.get_event_details() == {
        "title": "Team meeting",
        "date": "Next Friday",
        "time": "2pm",
    }
