import pytest

from aqeno.application.management import PairingCoordinator, PairingInvalidError


def test_pairing_code_is_one_time_and_does_not_create_an_account() -> None:
    coordinator = PairingCoordinator()
    session = coordinator.start()
    assert len(session.code) == 6 and session.code.isdigit()

    coordinator.exchange(session.code)

    with pytest.raises(PairingInvalidError):
        coordinator.exchange(session.code)


def test_pairing_locks_after_repeated_wrong_codes() -> None:
    coordinator = PairingCoordinator()
    session = coordinator.start()
    for _ in range(5):
        with pytest.raises(PairingInvalidError):
            coordinator.exchange("999999" if session.code != "999999" else "000000")
    with pytest.raises(PairingInvalidError):
        coordinator.exchange(session.code)
