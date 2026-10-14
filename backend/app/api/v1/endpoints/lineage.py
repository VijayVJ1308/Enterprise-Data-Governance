from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db
from lineage.lineage_service import LineageService
from lineage.impact_analysis import ImpactAnalysisEngine

router = APIRouter()


class AddNodeRequest(BaseModel):
    node_key: str
    name: str
    node_type: str  # DATASET, COLUMN, PIPELINE, DASHBOARD, REPORT
    domain: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class AddEdgeRequest(BaseModel):
    source_key: str
    target_key: str
    transformation_type: str = "DIRECT_TRANSFORM"
    pipeline_name: Optional[str] = None


@router.get("/graph", summary="Get Lineage Graph")
def get_lineage_graph(node_key: Optional[str] = None, db: Session = Depends(get_db)):
    """Retrieve full data lineage DAG nodes and edges."""
    return LineageService.get_lineage_graph(db, node_key=node_key)


@router.post("/node", summary="Add Lineage Node")
def add_lineage_node(req: AddNodeRequest, db: Session = Depends(get_db)):
    """Add a new node (Dataset, Column, Pipeline, Dashboard) to lineage graph."""
    node = LineageService.add_node(
        db,
        node_key=req.node_key,
        name=req.name,
        node_type=req.node_type,
        domain=req.domain,
        metadata_json=req.metadata_json,
    )
    return {
        "status": "success",
        "node_id": node.id,
        "node_key": node.node_key,
        "node_type": node.node_type,
    }


@router.post("/edge", summary="Add Lineage Edge")
def add_lineage_edge(req: AddEdgeRequest, db: Session = Depends(get_db)):
    """Add dependency relationship edge between two lineage nodes."""
    try:
        edge = LineageService.add_edge(
            db,
            source_key=req.source_key,
            target_key=req.target_key,
            transformation_type=req.transformation_type,
            pipeline_name=req.pipeline_name,
        )
        return {
            "status": "success",
            "edge_id": edge.id,
            "transformation_type": edge.transformation_type,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/impact/{target_node_key}", summary="Downstream & Upstream Impact Analysis")
def analyze_impact(target_node_key: str, db: Session = Depends(get_db)):
    """Perform downstream and upstream BFS dependency impact analysis on a target dataset/column."""
    try:
        return ImpactAnalysisEngine.analyze_impact(db, target_node_key)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
