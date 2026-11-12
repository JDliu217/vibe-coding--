import hashlib
import json
import math
import random
from datetime import datetime

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.orm import Session

from app.models import Account, Batch, Device, NetworkExit, PhoneNumber, Submission, SyntheticDevice
from app.schemas import StartIn, StateOut, StatsOut, SubmissionOut, TickIn

FAILURE_REASON = "注册请求被拒绝（验证码校验失败）"
STATUS_POOL = ("success", "success", "success", "success", "success", "failed")
DEFAULT_REUSE = 0.5
DEFAULT_BATCH_SIZE = 20
DEFAULT_INTERVAL_MS = 3000


class RegistrationError(Exception):
    def __init__(self, message: str, status_code: int = 409):
        self.message = message
        self.status_code = status_code


def _short_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:8]


def _webrtc_ip() -> str:
    return f"192.168.{random.randint(0, 255)}.{random.randint(2, 254)}"


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def read_state(session: Session) -> StateOut:
    total = session.scalar(select(func.count()).select_from(Submission)) or 0
    success = session.scalar(
        select(func.count()).select_from(Submission).where(Submission.status == "success")
    ) or 0
    rounds = session.scalar(select(func.coalesce(func.sum(Batch.round_count), 0))) or 0
    latest = session.scalars(select(Batch).order_by(Batch.id.desc())).first()
    if latest and latest.status == "running":
        status = "running"
    elif total:
        status = "done"
    else:
        status = "idle"

    rows = session.scalars(select(Submission).order_by(Submission.id.desc()).limit(50)).all()
    submissions = [_to_submission(row) for row in rows]
    return StateOut(
        status=status,
        batchId=latest.id if latest else None,
        reuseIntensity=float(latest.reuse_intensity) if latest else DEFAULT_REUSE,
        batchSize=latest.batch_size if latest else DEFAULT_BATCH_SIZE,
        intervalMs=latest.interval_ms if latest else DEFAULT_INTERVAL_MS,
        stats=StatsOut(total=total, success=success, failed=total - success, rounds=int(rounds)),
        submissions=submissions,
    )


def _to_submission(row: Submission) -> SubmissionOut:
    payload = row.payload_json or {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    device = payload.get("device") or {}
    network = payload.get("network") or {}
    created = payload.get("createdAt") or _stamp(row.created_at)
    return SubmissionOut(
        id=str(payload.get("id") or row.id),
        phone=str(payload.get("phone") or ""),
        createdAt=created,
        deviceId=str(device.get("deviceId") or ""),
        deviceModel=str(device.get("deviceModel") or ""),
        ip=str(network.get("ip") or ""),
        isp=str(network.get("isp") or ""),
        region=str(network.get("region") or ""),
        status=row.status,
    )


START_LOCK = "attack_console_start"


def start_batch(session: Session, body: StartIn) -> StateOut:
    # 检查和插入必须落在同一把连接锁里，否则两个请求会同时通过检查。
    acquired = session.execute(
        text("SELECT GET_LOCK(:name, :timeout)"),
        {"name": START_LOCK, "timeout": 10},
    ).scalar()
    if acquired != 1:
        raise RegistrationError("启动繁忙，请稍后重试")
    created_id = None
    try:
        running = session.scalar(select(Batch.id).where(Batch.status == "running").limit(1))
        if running:
            raise RegistrationError("已有注册任务在运行")
        batch = Batch(
            reuse_intensity=body.reuseIntensity,
            batch_size=body.batchSize,
            interval_ms=body.intervalMs,
            status="running",
            round_count=0,
            started_at=datetime.now().replace(microsecond=0),
            stopped_at=None,
        )
        session.add(batch)
        session.flush()
        created_id = batch.id
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.execute(text("SELECT RELEASE_LOCK(:name)"), {"name": START_LOCK})
    state = read_state(session)
    return state.model_copy(update={"batchId": created_id})


def stop_batch(session: Session, batch_id: int) -> StateOut:
    batch = session.get(Batch, batch_id)
    if batch and batch.status == "running":
        batch.status = "done"
        batch.stopped_at = datetime.now().replace(microsecond=0)
        session.commit()
    return read_state(session)


def reset_ledger(session: Session) -> StateOut:
    session.execute(delete(Submission))
    session.execute(delete(Account))
    session.execute(delete(SyntheticDevice))
    session.execute(delete(Batch))
    session.execute(update(PhoneNumber).values(status="available"))
    session.commit()
    return read_state(session)


def run_tick(session: Session, batch_id: int, body: TickIn) -> StateOut:
    try:
        batch = session.get(Batch, batch_id, with_for_update=True)
        if batch is None or batch.status != "running":
            raise RegistrationError("任务已停止")

        exits = list(session.scalars(select(NetworkExit)).all())
        devices = list(session.scalars(select(Device)).all())
        if not exits or not devices:
            raise RegistrationError("资源库还没有设备或出口 IP")

        distinct = max(1, math.ceil(len(exits) * (1 - body.reuseIntensity)))
        subset = random.sample(exits, distinct)
        phones = list(
            session.scalars(
                select(PhoneNumber)
                .where(PhoneNumber.status == "available")
                .order_by(PhoneNumber.id)
                .limit(body.batchSize)
                .with_for_update()
            ).all()
        )
        if len(phones) < body.batchSize:
            raise RegistrationError("手机号已用完，请重置后再注册")

        base = session.scalar(select(func.coalesce(func.max(SyntheticDevice.id), 0))) or 0
        moment = datetime.now().replace(microsecond=0)
        stamp = _stamp(moment)

        for index, phone in enumerate(phones, start=1):
            parent = random.choice(devices)
            chosen_ip = random.choice(subset)
            synthetic = _mint_synthetic(parent, batch.id, f"SYN-{base + index:05d}", moment)
            session.add(synthetic)
            session.flush()

            phone.status = "assigned"
            account = Account(
                batch_id=batch.id,
                synthetic_device_id=synthetic.id,
                phone_number_id=phone.id,
                network_exit_id=chosen_ip.id,
                email=f"user{phone.phone}@example.com",
                created_at=moment,
            )
            session.add(account)
            session.flush()

            status = random.choice(STATUS_POOL)
            reason = FAILURE_REASON if status == "failed" else None
            payload = {
                "id": f"REG-{account.id:05d}",
                "phone": phone.phone,
                "email": account.email,
                "status": status,
                "createdAt": stamp,
                "resultSource": "placeholder",
                "device": {
                    "deviceId": synthetic.synthetic_code,
                    "deviceModel": synthetic.device_model,
                    "parentDeviceId": parent.device_code,
                },
                "network": {
                    "ip": chosen_ip.ip,
                    "ipType": chosen_ip.ip_type,
                    "region": chosen_ip.region,
                    "isp": chosen_ip.isp,
                    "asn": chosen_ip.asn,
                },
                "failureReason": reason,
            }
            session.add(
                Submission(
                    batch_id=batch.id,
                    account_id=account.id,
                    payload_json=payload,
                    status=status,
                    failure_reason=reason,
                    result_source="placeholder",
                    created_at=moment,
                )
            )

        batch.reuse_intensity = body.reuseIntensity
        batch.batch_size = body.batchSize
        batch.round_count += 1
        session.commit()
    except Exception:
        session.rollback()
        raise
    return read_state(session)


def _mint_synthetic(parent: Device, batch_id: int, code: str, moment: datetime) -> SyntheticDevice:
    salt = f"{code}-{moment.timestamp()}-{random.random()}"
    return SyntheticDevice(
        batch_id=batch_id,
        parent_device_id=parent.id,
        synthetic_code=code,
        device_model=parent.device_model,
        os_version=parent.os_version,
        os_arch=parent.os_arch,
        browser_name=parent.browser_name,
        browser_version=parent.browser_version,
        user_agent=parent.user_agent,
        screen_resolution=parent.screen_resolution,
        color_depth=parent.color_depth,
        device_pixel_ratio=parent.device_pixel_ratio,
        platform=parent.platform,
        hardware_concurrency=parent.hardware_concurrency,
        device_memory=parent.device_memory,
        touch_support=parent.touch_support,
        webgl_renderer=parent.webgl_renderer,
        audio_context_fingerprint=_short_hash(parent.audio_context_fingerprint + salt),
        canvas_fingerprint=_short_hash(parent.canvas_fingerprint + salt),
        timezone=parent.timezone,
        language=parent.language,
        cookie_enabled=parent.cookie_enabled,
        local_storage_enabled=parent.local_storage_enabled,
        webrtc_local_ip=_webrtc_ip(),
        font_list_hash=parent.font_list_hash,
        created_at=moment,
    )
