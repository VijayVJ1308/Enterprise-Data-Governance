import logging
from typing import List, Dict, Any, Set
from sqlalchemy.orm import Session
from backend.app.models.lineage import LineageNode, LineageEdge

logger = logging.getLogger("ImpactAnalysisEngine")


class ImpactAnalysisEngine:

    @staticmethod
    def analyze_impact(db_session: Session, target_node_key: str) -> Dict[str, Any]:
        target_node = db_session.query(LineageNode).filter_by(node_key=target_node_key).first()
        if not target_node:
            raise ValueError(f"Target node '{target_node_key}' not found in lineage graph.")

        nodes = db_session.query(LineageNode).all()
        edges = db_session.query(LineageEdge).all()

        node_map = {n.id: n for n in nodes}
        key_map = {n.node_key: n for n in nodes}

        # Build adjacency maps
        downstream_adj: Dict[str, List[str]] = {n.id: [] for n in nodes}
        upstream_adj: Dict[str, List[str]] = {n.id: [] for n in nodes}

        for e in edges:
            downstream_adj[e.source_node_id].append(e.target_node_id)
            upstream_adj[e.target_node_id].append(e.source_node_id)

        # BFS Downstream Traversal
        visited_downstream: Set[str] = set()
        queue = [target_node.id]
        while queue:
            curr = queue.pop(0)
            for child in downstream_adj.get(curr, []):
                if child not in visited_downstream and child != target_node.id:
                    visited_downstream.add(child)
                    queue.append(child)

        # BFS Upstream Traversal
        visited_upstream: Set[str] = set()
        queue = [target_node.id]
        while queue:
            curr = queue.pop(0)
            for parent in upstream_adj.get(curr, []):
                if parent not in visited_upstream and parent != target_node.id:
                    visited_upstream.add(parent)
                    queue.append(parent)

        downstream_nodes = [node_map[nid] for nid in visited_downstream if nid in node_map]
        upstream_nodes = [node_map[nid] for nid in visited_upstream if nid in node_map]

        impacted_dashboards = [n.name for n in downstream_nodes if n.node_type in ["DASHBOARD", "REPORT"]]
        impacted_marts = [n.name for n in downstream_nodes if "mart" in n.name.lower() or "gold" in n.name.lower()]
        impacted_pipelines = list(set(e.pipeline_name for e in edges if e.pipeline_name and (e.source_node_id in visited_downstream or e.target_node_id in visited_downstream)))

        return {
            "target_node": {"key": target_node.node_key, "name": target_node.name, "type": target_node.node_type},
            "upstream_count": len(upstream_nodes),
            "downstream_count": len(downstream_nodes),
            "upstream_dependencies": [{"key": n.node_key, "name": n.name, "type": n.node_type} for n in upstream_nodes],
            "downstream_impact": [{"key": n.node_key, "name": n.name, "type": n.node_type} for n in downstream_nodes],
            "impacted_dashboards": impacted_dashboards,
            "impacted_marts": impacted_marts,
            "impacted_pipelines": impacted_pipelines,
        }
