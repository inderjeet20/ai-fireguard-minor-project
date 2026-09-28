"""
TC-06: Blocked-Road Handling
Synopsis Expectation:
Blocked segment clearly marked on the map; regenerated route excludes it;
an alternative traversable route is produced where one exists.
"""

from api.services.routing import router_service

def test_tc06_blocked_road_rerouting():
    # Baseline route from Dehradun to Rishikesh normally uses direct highway (e_ddn_rsh)
    baseline = router_service.compute_evacuation_routes(
        source_id="DEHRADUN",
        target_id="RISHIKESH",
        blocked_edges=[]
    )
    assert baseline["success"] is True
    assert "RISHIKESH" in baseline["safest_route"]["path_nodes"]

    # Now simulate road blockage on the primary highway between Dehradun and Rishikesh (e_ddn_rsh)
    blocked_test = router_service.compute_evacuation_routes(
        source_id="DEHRADUN",
        target_id="RISHIKESH",
        blocked_edges=["e_ddn_rsh"]
    )

    assert blocked_test["success"] is True
    rerouted_path = blocked_test["safest_route"]["path_nodes"]

    # Rerouted path must exclude the blocked edge and traverse through Haridwar
    assert "HARIDWAR" in rerouted_path
    assert rerouted_path == ["DEHRADUN", "HARIDWAR", "RISHIKESH"]

    # Distance should naturally increase reflecting detour
    assert blocked_test["safest_route"]["total_distance_km"] > baseline["safest_route"]["total_distance_km"]
