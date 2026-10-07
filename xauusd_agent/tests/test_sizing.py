import math

import pytest

from risk.sizing import loss_per_lot, position_size


def test_loss_per_lot_xauusd():
    # $5 stop on 100 oz = $500 per lot, + $0.10 slippage ×100 + $7 commission
    assert loss_per_lot(2000.0, 1995.0, 100) == pytest.approx(500.0)
    assert loss_per_lot(2000.0, 1995.0, 100, slippage=0.10, commission_per_lot_rt=7.0) == pytest.approx(517.0)
    assert loss_per_lot(1995.0, 2000.0, 100) == pytest.approx(500.0)  # short side symmetric


def test_loss_per_lot_rejects_zero_stop():
    with pytest.raises(ValueError):
        loss_per_lot(2000.0, 2000.0, 100)


def test_basic_size_rounds_down():
    # 10k × 0.5% = $50 budget; $517/lot → 0.0967 → 0.09 (never rounded up)
    r = position_size(10_000, 0.5, 517.0, 0.01, 50, 0.01)
    assert r.ok and r.volume == pytest.approx(0.09)
    assert r.risk_amount <= 50.0


def test_one_percent():
    r = position_size(10_000, 1.0, 500.0, 0.01, 50, 0.01)
    assert r.volume == pytest.approx(0.20)
    assert r.risk_amount == pytest.approx(100.0)


@pytest.mark.parametrize("equity,risk,per_lot", [(10_000, 0.5, 517), (2_345.67, 0.75, 333.3), (100_000, 1.0, 1234.5),
                                                  (5_000, 0.5, 150.0), (50_000, 1.0, 87.0)])
def test_risk_never_exceeds_budget(equity, risk, per_lot):
    r = position_size(equity, risk, per_lot, 0.01, 100, 0.01)
    assert r.ok
    assert r.risk_amount <= equity * risk / 100 + 1e-9
    # and adding one more step would exceed the budget (tightest valid size)
    assert (r.volume + 0.01) * per_lot > equity * risk / 100


def test_min_volume_exceeding_budget_is_rejected_not_rounded_up():
    # $1,000 × 0.5% = $5 budget, but 0.01 lot × $1,000/lot = $10 → reject
    r = position_size(1_000, 0.5, 1_000.0, 0.01, 50, 0.01)
    assert not r.ok
    assert "min volume" in r.reason


def test_capped_at_max_volume():
    r = position_size(10_000_000, 1.0, 100.0, 0.01, 50, 0.01)
    assert r.volume == pytest.approx(50.0)


def test_coarser_volume_step():
    r = position_size(10_000, 1.0, 300.0, 0.1, 50, 0.1)  # raw 0.333 → 0.3
    assert r.volume == pytest.approx(0.3)


@pytest.mark.parametrize("equity,risk,per_lot", [(0, 1, 500), (-5, 1, 500), (10_000, 0, 500), (10_000, 1, 0),
                                                  (10_000, 1, math.inf)])
def test_invalid_inputs_rejected(equity, risk, per_lot):
    assert not position_size(equity, risk, per_lot, 0.01, 50, 0.01).ok
