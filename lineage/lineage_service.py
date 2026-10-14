import logging
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from backend.app.models.lineage import LineageNode, LineageEdge

logger = logging.getLogger("LineageService")


class LineageService:

    @staticmethod
    def add_node(
        db_session: Session,
        node_key: str,
        name: str,
        node_type: str,  # DATASET, COLUMN, PIPELINE, DASHBOARD, REPORT
        domain: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> LineageNode:
        existing = db_session.query(LineageNode).filter_by(node_key=node_key).first()
        if existing:
            return existing

        node = LineageNode(
            node_key=node_key,
            name=name,
            node_type=node_type.upper(),
            domain=domain,
            metadata_json=metadata_json or {},
        )
        db_session.add(node)
        db_session.commit()
        db_session.refresh(node)
        logger.info(f"Added lineage node '{node_key}' ({node_type}).")
        return node

    @staticmethod
    def add_edge(
        db_session: Session,
        source_key: str,
        target_key: str,
        transformation_type: str = "DIRECT_TRANSFORM",
        pipeline_name: Optional[str] = None,
    ) -> LineageEdge:
        src_node = db_session.query(LineageNode).filter_by(node_key=source_key).first()
        tgt_node = db_session.query(LineageNode).filter_by(node_key=target_key).first()

        if not src_node or not tgt_node:
            raise ValueError(f"Source '{source_key}' or target '{target_key}' node missing from lineage graph.")

        existing_edge = db_session.query(LineageEdge).filter_by(
            source_node_id=src_node.id, target_node_id=tgt_node.id
        ).first()
        if existing_edge:
            return existing_edge

        edge = LineageEdge(
            source_node_id=src_node.id,
            target_node_id=tgt_node.id,
            transformation_type=transformation_type.upper(),
            pipeline_name=pipeline_name,
        )
        db_session.add(edge)
        db_session.commit()
        db_session.refresh(edge)
        logger.info(f"Added lineage edge '{source_key}' -> '{target_key}' via '{pipeline_name}'.")
        return edge

    @staticmethod
    def get_lineage_graph(db_session: Session, node_key: Optional[str] = None) -> Dict[str, Any]:
        nodes = db_session.query(LineageNode).all()
        edges = db_session.query(LineageEdge).all()

        nodes_dict = {n.id: {"id": n.id, "key": n.node_key, "name": n.name, "type": n.node_type, "domain": n.domain} for n in nodes}
        edges_list = [
            {
                "source": nodes_dict[e.source_node_id]["key"],
                "target": nodes_dict[e.target_node_id]["key"],
                "transformation_type": e.transformation_type,
                "pipeline_name": e.pipeline_name,
            }
            for e in edges
            if e.source_node_id in nodes_dict and e.target_node_id in nodes_dict
        ]

        return {
            "nodes": list(nodes_dict.values()),
            "edges": edges_list,
        }
