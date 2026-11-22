"""
tests/test_cultural_evolution.py
EON 2.0 â€” Tests for cultural trait registry, 6 transmission mechanisms,
and organic socio-economic fission triggers.
"""

import os
import pytest
from evolution.cultural_traits import (
    CulturalTrait, CulturalTraitRegistry, TransmissionType, TraitStatus,
)
from society.sovereignty import SocioEconomicFissionTrigger


def test_register_new_trait():
    """Register a trait, verify trait_id assigned and creator registered as first adopter."""
    reg = CulturalTraitRegistry()
    trait = reg.register_new_trait(
        name="Grain Futures Trading",
        category="economic",
        creator="Athena",
        day=1,
        description="Contracts promising future grain harvest for upfront tokens.",
        transmission_type=TransmissionType.SUCCESS,
        economic_effects={"yield_boost": 0.15},
    )
    assert trait.trait_id.startswith("trait_")
    assert trait.name == "Grain Futures Trading"
    assert trait.status == TraitStatus.EMERGING
    assert trait.adopter_count() == 1
    assert reg.get_trait(trait.trait_id) is trait


def test_record_adoption_and_adopter_count():
    """Record adoptions by multiple agents and check adopter_count updates."""
    reg = CulturalTraitRegistry()
    trait = reg.register_new_trait(
        name="Common Cistern Maintenance",
        category="social",
        creator="Solon",
        day=1,
        description="Clan-wide rotational labor for desilting cisterns.",
        transmission_type=TransmissionType.CONFORMIST,
    )
    assert trait.adopter_count() == 1

    reg.record_adoption(trait.trait_id, "Hermes", day=2, source_agent="Solon")
    reg.record_adoption(trait.trait_id, "Prometheus", day=2, source_agent="Solon")
    assert trait.adopter_count() == 3

    # Duplicate adoption by same agent should not inflate unique count
    reg.record_adoption(trait.trait_id, "Hermes", day=3, source_agent="Solon")
    assert trait.adopter_count() == 3


def test_transformation_creates_lineage():
    """A transformed trait points to its parent and parent records child in transformed_traits."""
    reg = CulturalTraitRegistry()
    parent = reg.register_new_trait(
        name="Barter Exchange",
        category="economic",
        creator="Orion",
        day=1,
        description="Direct exchange of water for grain.",
        transmission_type=TransmissionType.HORIZONTAL,
    )

    child = CulturalTrait(
        trait_id="trait_monetary_exchange",
        name="Monetized Token Exchange",
        category="economic",
        creator_agent="Dione",
        origin_day=3,
        description="Pricing all goods in standard EON tokens.",
        transmission_type=TransmissionType.PRESTIGE,
    )

    reg.record_transformation(parent.trait_id, child)
    assert child.parent_trait_id == parent.trait_id
    assert child.trait_id in parent.transformed_traits
    assert reg.get_trait(child.trait_id) is child


def test_extinction_marks_status():
    """record_extinction marks trait EXTINCT and removes it from active list."""
    reg = CulturalTraitRegistry()
    trait = reg.register_new_trait(
        name="Sunken Granary Storage",
        category="technology",
        creator="Lysander",
        day=1,
        description="Storing grain in deep earthen pits.",
        transmission_type=TransmissionType.OBLIQUE,
    )
    assert trait in reg.get_active_traits()

    reg.record_extinction(trait.trait_id, day=5)
    assert trait.status == TraitStatus.EXTINCT
    assert trait not in reg.get_active_traits()
    # Adoptions to extinct traits should fail
    assert reg.record_adoption(trait.trait_id, "Phaedra", day=6) is False


def test_six_transmission_types_valid():
    """Verify all 6 required cultural transmission modes exist."""
    expected = {
        "vertical", "horizontal", "oblique", "prestige", "success", "conformist"
    }
    actual = {t.value for t in TransmissionType}
    assert actual == expected


def test_trait_persistence_roundtrip(tmp_path):
    """save_state and load_state must roundtrip active and mutated traits."""
    reg1 = CulturalTraitRegistry()
    t1 = reg1.register_new_trait(
        name="Ancestral Veneration",
        category="religious",
        creator="Calliope",
        day=1,
        description="Formal recitation of founding lineage.",
        transmission_type=TransmissionType.VERTICAL,
    )
    reg1.record_adoption(t1.trait_id, "Nikias", day=2, source_agent="Calliope")

    state_file = str(tmp_path / "cultural_traits.json")
    reg1.save_state(state_file)
    assert os.path.exists(state_file)

    reg2 = CulturalTraitRegistry()
    loaded = reg2.load_state(state_file)
    assert loaded is True

    t2 = reg2.get_trait(t1.trait_id)
    assert t2 is not None
    assert t2.name == t1.name
    assert t2.adopter_count() == 2
    assert t2.transmission_type == TransmissionType.VERTICAL


def test_gini_fission_trigger():
    """Gini trigger fires when wealth inequality > 0.45."""
    trigger = SocioEconomicFissionTrigger()

    # Equal wealth: Gini = 0.0 -> False
    equal_balances = {"A": 500, "B": 500, "C": 500, "D": 500}
    assert trigger.check_gini_trigger("clan_alpha", equal_balances) is False

    # Extreme inequality: Gini > 0.45 -> True
    skewed_balances = {"A": 10, "B": 20, "C": 30, "D": 2000}
    assert trigger.check_gini_trigger("clan_alpha", skewed_balances) is True


def test_petition_fission_trigger():
    """Petition trigger fires when >= 30% of members sign."""
    trigger = SocioEconomicFissionTrigger()
    total_members = 10

    # 2 out of 10 = 20% -> False
    assert trigger.check_petition_trigger(["A", "B"], total_members) is False

    # 3 out of 10 = 30% -> True
    assert trigger.check_petition_trigger(["A", "B", "C"], total_members) is True
