from helpers import make_hub, wait_for


def test_button_state_follows_notifications():
    hub, sim = make_hub()
    with hub:
        assert hub.button.is_released and not hub.button.is_pressed
        sim.press()
        assert wait_for(lambda: hub.button.is_pressed)
        assert not hub.button.is_released
        sim.release()
        assert wait_for(lambda: hub.button.is_released)


def test_initial_state_is_read_on_connect():
    hub, sim = make_hub()
    sim.button = True
    with hub:
        assert hub.button.is_pressed
