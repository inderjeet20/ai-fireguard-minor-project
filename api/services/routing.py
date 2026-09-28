"""
Risk-Aware Safe Evacuation Routing Engine for AI FireGuard.
Uses NetworkX to implement Dijkstra / A* algorithms on a risk-weighted graph.
Demonstrates: 'The shortest route is not necessarily the safest route.'
Supports dynamic road blockages and multi-criteria route evaluation.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import networkx as nx

from api.config import DATA_DIR, SAFE_DESTINATIONS

ROAD_NETWORK_FILE = DATA_DIR / "road_network.json"

class RiskAwareRouter:
    def __init__(self, risk_multiplier: float = 6.0):
        self.risk_multiplier = risk_multiplier
        self.network_data = self._load_network_data()
        self.nodes_dict = {n["id"]: n for n in self.network_data.get("nodes", [])}
        self.edges_list = self.network_data.get("edges", [])

    def _load_network_data(self) -> Dict[str, Any]:
        if ROAD_NETWORK_FILE.exists():
            with open(ROAD_NETWORK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"nodes": [], "edges": []}

    def get_network_overview(self) -> Dict[str, Any]:
        """Returns nodes, edges, and designated safe shelter locations."""
        return {
            "region": "Uttarakhand, India",
            "nodes": list(self.nodes_dict.values()),
            "edges": self.edges_list,
            "shelters": SAFE_DESTINATIONS
        }

    def build_graph(self, blocked_edges: Optional[List[str]] = None, active_hotspot_weight: float = 1.0) -> nx.Graph:
        """
        Builds a NetworkX graph with two edge attributes:
        1. 'length': pure road distance in km
        2. 'risk_adjusted_weight': distance * (1 + alpha * hazard)
        """
        blocked_set = set(blocked_edges or [])
        G = nx.Graph()

        # Add nodes
        for node_id, node_info in self.nodes_dict.items():
            G.add_node(node_id, **node_info)

        # Add edges
        for edge in self.edges_list:
            edge_id = edge["id"]
            if edge_id in blocked_set:
                # Segment is impassable due to active roadblock / tree fall
                continue

            u = edge["u"]
            v = edge["v"]
            dist = float(edge["distance_km"])
            hazard = float(edge.get("base_hazard", 0.1)) * active_hotspot_weight

            # Risk-aware cost formula:
            # Cost = Distance * (1 + alpha * Risk)
            # High risk causes a heavy routing penalty
            risk_cost = dist * (1.0 + self.risk_multiplier * (hazard ** 1.5))

            G.add_edge(
                u, v,
                id=edge_id,
                length=dist,
                hazard=hazard,
                weight=risk_cost,
                road_name=edge.get("road_name", "Local Route")
            )

        return G

    def compute_evacuation_routes(
        self,
        source_id: str,
        target_id: str,
        blocked_edges: Optional[List[str]] = None,
        risk_multiplier: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Computes both:
        1. Direct / Shortest route (minimizes geometric distance only)
        2. AI Risk-Aware Safest route (minimizes distance penalized by fire hazard)
        """
        if risk_multiplier is not None:
            self.risk_multiplier = risk_multiplier

        if source_id not in self.nodes_dict:
            raise ValueError(f"Unknown starting location: {source_id}")
        if target_id not in self.nodes_dict:
            raise ValueError(f"Unknown destination location: {target_id}")

        G = self.build_graph(blocked_edges=blocked_edges)

        if not nx.has_path(G, source_id, target_id):
            return {
                "success": False,
                "error": f"No traversable road corridor between {self.nodes_dict[source_id]['name']} and {self.nodes_dict[target_id]['name']} with current road blockages."
            }

        # 1. Pure Shortest Path (distance only)
        shortest_path_nodes = nx.shortest_path(G, source=source_id, target=target_id, weight="length")
        shortest_summary = self._summarize_path(G, shortest_path_nodes, "Shortest Route (Distance Priority)")

        # 2. Safest Path (risk-weighted Dijkstra)
        safest_path_nodes = nx.shortest_path(G, source=source_id, target=target_id, weight="weight")
        safest_summary = self._summarize_path(G, safest_path_nodes, "Safest Route (AI Risk-Aware)")

        # Comparison metrics proving synopsis thesis
        risk_reduction = 0.0
        if shortest_summary["average_hazard"] > 0:
            diff = shortest_summary["average_hazard"] - safest_summary["average_hazard"]
            risk_reduction = round(max(0.0, (diff / shortest_summary["average_hazard"]) * 100), 1)

        is_different = shortest_path_nodes != safest_path_nodes

        return {
            "success": True,
            "source": self.nodes_dict[source_id],
            "destination": self.nodes_dict[target_id],
            "shortest_route": shortest_summary,
            "safest_route": safest_summary,
            "comparison": {
                "paths_are_identical": not is_different,
                "distance_difference_km": round(safest_summary["total_distance_km"] - shortest_summary["total_distance_km"], 1),
                "hazard_exposure_reduction_pct": risk_reduction,
                "thesis_verified": is_different and (safest_summary["average_hazard"] < shortest_summary["average_hazard"]),
                "recommendation": (
                    "Safest AI Detour strongly recommended: bypasses severe active fire hazard zone."
                    if is_different and safest_summary["average_hazard"] < shortest_summary["average_hazard"]
                    else "Direct corridor is clear of critical fire hazards; standard shortest route is safe."
                )
            },
            "active_blocked_edges": blocked_edges or []
        }

    def _summarize_path(self, G: nx.Graph, path_nodes: List[str], label: str) -> Dict[str, Any]:
        """Summarizes waypoints, distance, and fire hazard along a node sequence."""
        total_dist = 0.0
        total_hazard_weighted = 0.0
        segments = []
        coordinates = []

        for i in range(len(path_nodes)):
            node_id = path_nodes[i]
            node_info = self.nodes_dict[node_id]
            coordinates.append([node_info["lat"], node_info["lon"]])

            if i < len(path_nodes) - 1:
                next_id = path_nodes[i + 1]
                edge_data = G[node_id][next_id]
                seg_len = edge_data["length"]
                seg_hazard = edge_data["hazard"]
                total_dist += seg_len
                total_hazard_weighted += seg_hazard * seg_len

                segments.append({
                    "from_node": self.nodes_dict[node_id]["name"],
                    "to_node": self.nodes_dict[next_id]["name"],
                    "edge_id": edge_data["id"],
                    "distance_km": seg_len,
                    "hazard_level": round(seg_hazard, 2),
                    "road_name": edge_data["road_name"]
                })

        avg_hazard = round(total_hazard_weighted / total_dist, 2) if total_dist > 0 else 0.0
        
        # Qualitative Safety Score
        if avg_hazard < 0.25:
            safety_rating = "High Safety (Minimal Fire Threat)"
            badge_color = "#10b981"
        elif avg_hazard < 0.55:
            safety_rating = "Moderate Safety (Low-to-Mid Exposure)"
            badge_color = "#f59e0b"
        else:
            safety_rating = "Hazardous (Direct Fire Zone Exposure)"
            badge_color = "#ef4444"

        return {
            "label": label,
            "path_nodes": path_nodes,
            "path_names": [self.nodes_dict[nid]["name"] for nid in path_nodes],
            "total_distance_km": round(total_dist, 1),
            "estimated_travel_minutes": int(round((total_dist / 40.0) * 60)), # Average 40km/h hill road speed
            "average_hazard": avg_hazard,
            "safety_rating": safety_rating,
            "badge_color": badge_color,
            "coordinates": coordinates,
            "segments": segments
        }

router_service = RiskAwareRouter()
