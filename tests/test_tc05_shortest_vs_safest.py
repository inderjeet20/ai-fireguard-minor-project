"""
TC-05: Shortest Route versus Safest Route
Synopsis Expectation:
The geometrically shorter route is not automatically selected; the longer route avoiding
the high-risk zone is recommended, its risk-adjusted cost being lower;
the route is displayed alongside the risk zones.
"""

from api.services.routing import router_service

def test_tc05_shortest_vs_safest_evacuation_routing():
    # Route from Rishikesh to Srinagar (Garhwal)
    # The direct path (NH-7 Gorge) has an active hazard score of 0.88.
    # The alternate mountain detour (via Chamba/Tehri) has a much lower hazard of 0.14.
    res = router_service.compute_evacuation_routes(
        source_id="RISHIKESH",
        target_id="SRINAGAR",
        risk_multiplier=6.0
    )

    assert res["success"] is True
    shortest = res["shortest_route"]
    safest = res["safest_route"]
    comp = res["comparison"]

    # Safest route must have lower average hazard exposure than direct shortest route
    assert safest["average_hazard"] < shortest["average_hazard"]

    # Paths should be distinct to demonstrate detour capability
    assert shortest["path_nodes"] != safest["path_nodes"]

    # Thesis is verified: AI safely detours around the high danger zone
    assert comp["thesis_verified"] is True
    assert comp["hazard_exposure_reduction_pct"] > 50.0 # Substantial hazard drop
