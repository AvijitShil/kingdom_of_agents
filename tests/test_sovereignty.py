import pytest
from society.sovereignty import FissionEngine, SovereignKingdom


def test_fission_engine_threshold():
    engine = FissionEngine()
    # Below threshold (19) -> No fission
    k1 = engine.check_and_execute_fission("clan_alpha_technocrats", current_headcount=19)
    assert k1 is None
    assert len(engine.get_kingdoms()) == 0

    # At or above threshold (20) -> Fission into independent kingdom
    k2 = engine.check_and_execute_fission("clan_alpha_technocrats", current_headcount=20)
    assert k2 is not None
    assert isinstance(k2, SovereignKingdom)
    assert k2.population == 10
    assert "clan_alpha_technocrats" in k2.hostile_factions
    assert len(engine.get_kingdoms()) == 1


def test_sovereignty_persistence(tmp_path):
    engine = FissionEngine()
    engine.check_and_execute_fission("clan_beta_merchants", current_headcount=24)
    assert len(engine.get_kingdoms()) == 1

    save_file = str(tmp_path / "sovereignty_state.json")
    engine.save_state(save_file)

    new_engine = FissionEngine()
    loaded = new_engine.load_state(save_file)
    assert loaded is True
    assert len(new_engine.get_kingdoms()) == 1
    assert "clan_beta_merchants" == new_engine.get_kingdoms()[0].parent_clan
