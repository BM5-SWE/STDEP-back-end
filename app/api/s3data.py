"""
S3 Data API — Proxies S3 reads/writes and Step Function triggers
for the STDEP frontend dashboard.
"""

import json
import os
import boto3
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from app.api.auth import get_current_user
from app.models.user import User
from app.models.query_history import QueryHistory
from app.db.session import SessionLocal

router = APIRouter()

AWS_REGION = os.getenv("AWS_REGION", "ca-central-1")
s3 = boto3.client("s3", region_name=AWS_REGION)
sfn = boto3.client("stepfunctions", region_name=AWS_REGION)

ALIX_SCORED_BUCKET = "stdep-alix-scored-data"
AMAZON_SCORED_BUCKET = "stdep-amazon-scored-data"
ALIX_WEEKLY_TOP_BUCKET = "stdep-alix-weekly-top"
CATEGORIES_BUCKET = "stdep-categories"

ALIX_SFN_ARN = "arn:aws:states:ca-central-1:138228122605:stateMachine:stdep-alix-pipeline"
AMAZON_SFN_ARN = "arn:aws:states:ca-central-1:138228122605:stateMachine:stdep-amazon-pipeline"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _read_s3_json(bucket: str, key: str):
    try:
        resp = s3.get_object(Bucket=bucket, Key=key)
        return json.loads(resp["Body"].read().decode("utf-8"))
    except s3.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail=f"Key not found: {key}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 read error: {str(e)}")


def _write_s3_json(bucket: str, key: str, data: dict):
    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(data, indent=2, ensure_ascii=False),
            ContentType="application/json",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 write error: {str(e)}")


def _list_s3_keys(bucket: str, prefix: str = "") -> list[str]:
    try:
        keys = []
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return keys
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 list error: {str(e)}")


def _record_query_history(
    db: Session,
    user_id,
    query_text: str,
    platform: str,
    s3_key: str,
    product_count: int = 0,
    num_clusters: int = 0,
):
    """Record a completed search to the query_history table."""
    try:
        record = QueryHistory(
            user_id=user_id,
            query_text=query_text,
            platform=platform,
            query_type="custom",
            s3_result_key=s3_key,
            result_cached_at=datetime.now(timezone.utc),
            total_products_returned=product_count,
            num_clusters=num_clusters,
        )
        db.add(record)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[WARN] Failed to record query history: {e}")


# ═════════════════════════════════════════════════
# CATEGORIES
# ═════════════════════════════════════════════════

@router.get("/categories")
def get_categories(current_user: User = Depends(get_current_user)):
    return _read_s3_json(CATEGORIES_BUCKET, "category_definitions.json")


class NewCategoryRequest(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=100)


@router.post("/categories", status_code=201)
def create_category(payload: NewCategoryRequest, current_user: User = Depends(get_current_user)):
    data = _read_s3_json(CATEGORIES_BUCKET, "category_definitions.json")
    categories = data.get("categories", [])
    if any(c["id"] == payload.id for c in categories):
        raise HTTPException(status_code=409, detail="Category ID already exists")
    categories.append({"id": payload.id, "label": payload.label, "is_user_generated": True, "suggested_items": []})
    data["categories"] = categories
    data["_meta"]["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_s3_json(CATEGORIES_BUCKET, "category_definitions.json", data)
    return {"status": "created", "id": payload.id}


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: str, current_user: User = Depends(get_current_user)):
    data = _read_s3_json(CATEGORIES_BUCKET, "category_definitions.json")
    categories = data.get("categories", [])
    target = next((c for c in categories if c["id"] == category_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Category not found")
    if not target.get("is_user_generated", False):
        raise HTTPException(status_code=403, detail="Cannot delete system categories")
    data["categories"] = [c for c in categories if c["id"] != category_id]
    data["_meta"]["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_s3_json(CATEGORIES_BUCKET, "category_definitions.json", data)
    return None


# ═════════════════════════════════════════════════
# FAVOURITES (focus files)
# ═════════════════════════════════════════════════

@router.get("/favourites/{platform}")
def get_favourites(platform: str, current_user: User = Depends(get_current_user)):
    if platform not in ("amazon", "aliexpress"):
        raise HTTPException(status_code=400, detail="Platform must be 'amazon' or 'aliexpress'")
    key = f"focus_{platform}.json"
    try:
        return _read_s3_json(CATEGORIES_BUCKET, key)
    except HTTPException as e:
        if e.status_code == 404:
            return {"favourites": []}
        raise


class FavouriteRequest(BaseModel):
    category_id: str = "uncategorized"
    query: str
    source: str = "manual"


@router.post("/favourites/{platform}", status_code=201)
def add_favourite(platform: str, payload: FavouriteRequest, current_user: User = Depends(get_current_user)):
    if platform not in ("amazon", "aliexpress"):
        raise HTTPException(status_code=400, detail="Platform must be 'amazon' or 'aliexpress'")
    key = f"focus_{platform}.json"
    try:
        data = _read_s3_json(CATEGORIES_BUCKET, key)
    except HTTPException:
        data = {"favourites": []}
    favourites = data.get("favourites", [])
    existing = next((f for f in favourites if f["query"].lower() == payload.query.lower()), None)
    if existing:
        existing["category_id"] = payload.category_id
        existing["is_favourite"] = True
    else:
        favourites.append({
            "category_id": payload.category_id,
            "query": payload.query,
            "source": payload.source,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "is_favourite": True,
        })
    data["favourites"] = favourites
    _write_s3_json(CATEGORIES_BUCKET, key, data)

    # ── Also add the query to category_definitions.json suggested_items ──
    if payload.category_id and payload.category_id != "uncategorized":
        try:
            cat_data = _read_s3_json(CATEGORIES_BUCKET, "category_definitions.json")
            categories = cat_data.get("categories", [])
            for cat in categories:
                if cat["id"] == payload.category_id:
                    items = cat.get("suggested_items", [])
                    # Only add if not already present (case-insensitive)
                    if not any(item.lower() == payload.query.lower() for item in items):
                        items.append(payload.query)
                        cat["suggested_items"] = items
                        cat_data["_meta"]["updated_at"] = datetime.now(timezone.utc).isoformat()
                        _write_s3_json(CATEGORIES_BUCKET, "category_definitions.json", cat_data)
                    break
        except Exception:
            pass  # Non-critical — don't fail the favourite save

    return {"status": "added", "query": payload.query}


@router.delete("/favourites/{platform}/{query}")
def remove_favourite(platform: str, query: str, current_user: User = Depends(get_current_user)):
    if platform not in ("amazon", "aliexpress"):
        raise HTTPException(status_code=400, detail="Platform must be 'amazon' or 'aliexpress'")
    key = f"focus_{platform}.json"
    try:
        data = _read_s3_json(CATEGORIES_BUCKET, key)
    except HTTPException:
        raise HTTPException(status_code=404, detail="No favourites found")
    favourites = data.get("favourites", [])
    data["favourites"] = [f for f in favourites if f["query"].lower() != query.lower()]
    _write_s3_json(CATEGORIES_BUCKET, key, data)
    return {"status": "removed", "query": query}


# ═════════════════════════════════════════════════
# WEEKLY TOP 50 (AliExpress)
# ═════════════════════════════════════════════════

@router.get("/weekly-top")
def get_weekly_top(current_user: User = Depends(get_current_user)):
    keys = _list_s3_keys(ALIX_WEEKLY_TOP_BUCKET)
    if not keys:
        raise HTTPException(status_code=404, detail="No weekly top data found")
    keys.sort(reverse=True)
    latest_key = keys[0]
    return _read_s3_json(ALIX_WEEKLY_TOP_BUCKET, latest_key)


# ═════════════════════════════════════════════════
# SCORED DATA (read results from S3)
# ═════════════════════════════════════════════════

@router.get("/scored/{platform}")
def list_scored_queries(
    platform: str,
    query_slug: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    if platform not in ("amazon", "aliexpress"):
        raise HTTPException(status_code=400, detail="Platform must be 'amazon' or 'aliexpress'")
    bucket = AMAZON_SCORED_BUCKET if platform == "amazon" else ALIX_SCORED_BUCKET
    prefix = f"{date}/" if date else ""
    keys = _list_s3_keys(bucket, prefix)
    if query_slug:
        slug = query_slug.replace(" ", "_").lower()
        keys = [k for k in keys if slug in k.lower()]
    results = []
    for key in keys:
        parts = key.split("/")
        if len(parts) >= 2:
            results.append({"key": key, "date": parts[0], "filename": parts[1]})
    results.sort(key=lambda x: x["key"], reverse=True)
    return {"platform": platform, "count": len(results), "files": results}


@router.get("/scored/{platform}/latest")
def get_latest_scored(
    platform: str,
    query: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    if platform not in ("amazon", "aliexpress"):
        raise HTTPException(status_code=400, detail="Platform must be 'amazon' or 'aliexpress'")
    bucket = AMAZON_SCORED_BUCKET if platform == "amazon" else ALIX_SCORED_BUCKET
    slug = query.replace(" ", "_").lower()
    keys = _list_s3_keys(bucket)
    matching = [k for k in keys if slug in k.lower()]
    if not matching:
        return {"found": False, "platform": platform, "query": query}
    matching.sort(reverse=True)
    latest_key = matching[0]
    data = _read_s3_json(bucket, latest_key)
    return {"found": True, "platform": platform, "query": query, "key": latest_key, "data": data}


@router.get("/scored/{platform}/file")
def get_scored_file(
    platform: str,
    key: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    if platform not in ("amazon", "aliexpress"):
        raise HTTPException(status_code=400, detail="Platform must be 'amazon' or 'aliexpress'")
    bucket = AMAZON_SCORED_BUCKET if platform == "amazon" else ALIX_SCORED_BUCKET
    return _read_s3_json(bucket, key)


# ═════════════════════════════════════════════════
# SEARCH (trigger Step Functions)
# ═════════════════════════════════════════════════

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    platform: str = Field(pattern="^(amazon|aliexpress)$")


@router.post("/search")
def trigger_search(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bucket = AMAZON_SCORED_BUCKET if payload.platform == "amazon" else ALIX_SCORED_BUCKET
    slug = payload.query.replace(" ", "_").lower()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Check for cached results from today
    keys = _list_s3_keys(bucket, prefix=f"{today}/")
    cached = [k for k in keys if slug in k.lower()]

    if cached:
        cached.sort(reverse=True)
        data = _read_s3_json(bucket, cached[0])
        product_count = data.get("count", len(data.get("products", [])))
        cluster_legend = data.get("cluster_legend", {})
        # Record to query history
        _record_query_history(
            db, current_user.id, payload.query, payload.platform,
            cached[0], product_count, len(cluster_legend),
        )
        return {"status": "cached", "key": cached[0], "data": data}

    # No cache — trigger Step Function
    arn = AMAZON_SFN_ARN if payload.platform == "amazon" else ALIX_SFN_ARN

    if payload.platform == "amazon":
        sfn_input = {"query": payload.query, "pages": [1], "max_asins": 48}
    else:
        sfn_input = {"query": payload.query, "page": "1"}

    try:
        response = sfn.start_execution(stateMachineArn=arn, input=json.dumps(sfn_input))
        return {
            "status": "started",
            "execution_arn": response["executionArn"],
            "query": payload.query,
            "platform": payload.platform,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {str(e)}")


class SearchStatusRequest(BaseModel):
    execution_arn: str
    query: str
    platform: str = Field(pattern="^(amazon|aliexpress)$")


@router.post("/search/status")
def check_search_status(
    payload: SearchStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        response = sfn.describe_execution(executionArn=payload.execution_arn)
        status = response["status"]

        if status == "SUCCEEDED":
            bucket = AMAZON_SCORED_BUCKET if payload.platform == "amazon" else ALIX_SCORED_BUCKET
            slug = payload.query.replace(" ", "_").lower()
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            keys = _list_s3_keys(bucket, prefix=f"{today}/")
            matching = [k for k in keys if slug in k.lower()]

            if matching:
                matching.sort(reverse=True)
                data = _read_s3_json(bucket, matching[0])
                product_count = data.get("count", len(data.get("products", [])))
                cluster_legend = data.get("cluster_legend", {})
                # Record to query history
                _record_query_history(
                    db, current_user.id, payload.query, payload.platform,
                    matching[0], product_count, len(cluster_legend),
                )
                return {"status": "completed", "key": matching[0], "data": data}

            return {"status": "completed", "data": None, "message": "Pipeline finished but no scored file found yet"}

        elif status == "FAILED":
            error = response.get("error", "Unknown error")
            cause = response.get("cause", "")
            return {"status": "failed", "error": error, "cause": cause}

        else:
            return {"status": "running"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check status: {str(e)}")
