"""
TC-04: Basic Evacuation Route Generation
Synopsis Expectation:
A route of genuine, connected graph edges is generated between source and destination,
traced continuously on the map with summary information such as total distance.
"""

from api.services.routing import router_service

def test_tc04_basic_evacuation_routing():
    # Route from Dehradun to Haridwar
    res = router_service.compute_evacuation_routes(
        source_id="DEHRADUN",
        target_id="HARIDWAR"
    )

    assert res["success"] is True
    shortest = res["shortest_route"]
    
    # Path must be a non-empty sequence of connected nodes
    path_nodes = shortest["path_nodes"]
    assert len(path_nodes) >= 2
    assert path_nodes[0] == "DEHRADUN"
    assert path_nodes[-1] == "HARIDWAR"

    # Metric summaries must exist and be positive
    assert shortest["total_distance_km"] > 0
    assert shortest["estimated_travel_minutes"] > 0
    assert len(shortest["coordinates"]) == len(path_nodes)
    assert len(shortest["segments"]) == len(path_nodes) - 1
