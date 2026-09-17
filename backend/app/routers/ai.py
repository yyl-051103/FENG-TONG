"""
AI 助手路由 — 创作辅助 / 个人记录 / 删除记录
"""
import traceback
import requests
import sys

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.ai_record import AICreationRecord
from app.schemas.news import AIAssistRequest
from app.config import DIFY_CREATIVE_API_KEY, DIFY_API_URL

router = APIRouter()


def _log(msg: str):
    print(f"[Dify-创意] {msg}", file=sys.stderr, flush=True)


def call_dify_agent(content: str, assist_type: str, title: str) -> str:
    headers = {
        "Authorization": f"Bearer {DIFY_CREATIVE_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "inputs": {
            "zhu_ti": title,
            "nei_rong": content,
            "xuan_xiang": assist_type,
        },
        "response_mode": "blocking",
        "user": "user",
    }
    try:
        _log(f"调用中: title={title[:30]}, type={assist_type}")
        res = requests.post(DIFY_API_URL, json=data, headers=headers, timeout=60)
        _log(f"响应: status={res.status_code}, body前500={res.text[:500]}")
        resp_json = res.json()
        outputs = resp_json.get("data", {}).get("outputs", {})
        if "text" not in outputs:
            _log(f"失败: outputs中缺少text字段, 实际outputs={outputs}")
            _log(f"完整响应: {res.text[:1000]}")
            return f"【{assist_type}】（AI处理异常，请联系管理员检查Dify工作流配置）"
        result = outputs["text"]
        _log(f"成功: output长度={len(result)}")
        return result
    except requests.Timeout:
        _log("失败: 请求Dify超时")
        return f"【{assist_type}】（AI处理超时，请稍后重试）"
    except Exception as e:
        _log(f"失败: {type(e).__name__}: {e}")
        _log(f"Traceback: {traceback.format_exc()}")
        return f"【{assist_type}】{content}"


@router.post("/assist")
def ai_assist(
    req: AIAssistRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI 创作辅助"""
    result = call_dify_agent(req.original_content, req.assist_type, req.title)
    record = AICreationRecord(
        original_content=req.original_content,
        optimized_content=result,
        assist_type=req.assist_type,
        user_id=user.id,
    )
    db.add(record)
    db.commit()
    return {"optimized_content": result, "create_time": record.create_time}


@router.get("/record")
def get_ai_records(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """个人 AI 辅助记录"""
    return (
        db.query(AICreationRecord)
        .filter(AICreationRecord.user_id == user.id)
        .order_by(AICreationRecord.create_time.desc())
        .all()
    )


@router.delete("/record/{record_id}")
def del_ai_record(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除个人 AI 记录"""
    rec = (
        db.query(AICreationRecord)
        .filter(
            AICreationRecord.id == record_id,
            AICreationRecord.user_id == user.id,
        )
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404)
    db.delete(rec)
    db.commit()
    return {"code": 200}
