from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


# --- DB Instance ---

class DbInstanceListItem(BaseModel):
    id: int
    instance_name: str
    db_type: str = "oracle"
    host: str | None = None
    port: int | None = None
    service_name: str | None = None
    environment: str | None = None
    status: str = "unknown"
    is_active: int = 1
    last_seen_at: datetime | None = None

    model_config = {"from_attributes": True}


class DbInstanceDetail(DbInstanceListItem):
    support_group: str | None = None
    created_at: datetime | None = None
    tablespaces: list[TablespaceItem] = []
    performance: DbPerformanceItem | None = None
    sessions_summary: DbSessionsSummary | None = None
    slow_queries: list[SlowQueryItem] = []


# --- Tablespace ---

class TablespaceItem(BaseModel):
    id: int
    tablespace_name: str
    total_mb: float | None = None
    used_mb: float | None = None
    free_mb: float | None = None
    used_percent: float | None = None
    autoextensible: str | None = None
    max_mb: float | None = None
    status: str | None = None
    collected_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Performance ---

class DbPerformanceItem(BaseModel):
    buffer_cache_hit_ratio: float | None = None
    library_cache_hit_ratio: float | None = None
    parse_count_total: int | None = None
    hard_parse_count: int | None = None
    execute_count: int | None = None
    user_commits: int | None = None
    user_rollbacks: int | None = None
    physical_reads: int | None = None
    physical_writes: int | None = None
    redo_size: int | None = None
    sga_total_mb: float | None = None
    pga_total_mb: float | None = None
    active_sessions: int | None = None
    inactive_sessions: int | None = None
    total_sessions: int | None = None
    max_sessions: int | None = None
    db_uptime_seconds: int | None = None
    collected_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Sessions ---

class DbSessionItem(BaseModel):
    id: int
    sid: int | None = None
    serial_no: int | None = None
    username: str | None = None
    program: str | None = None
    machine: str | None = None
    status: str | None = None
    sql_id: str | None = None
    sql_text: str | None = None
    wait_class: str | None = None
    wait_event: str | None = None
    seconds_in_wait: float | None = None
    blocking_session: int | None = None
    logon_time: datetime | None = None
    elapsed_seconds: float | None = None
    collected_at: datetime | None = None

    model_config = {"from_attributes": True}


class DbSessionsSummary(BaseModel):
    active: int = 0
    inactive: int = 0
    total: int = 0
    blocking_count: int = 0
    long_running_count: int = 0  # > 60 seconds


# --- Slow Queries ---

class SlowQueryItem(BaseModel):
    id: int
    sql_id: str | None = None
    sql_text: str | None = None
    username: str | None = None
    elapsed_seconds: float | None = None
    cpu_seconds: float | None = None
    buffer_gets: int | None = None
    disk_reads: int | None = None
    rows_processed: int | None = None
    executions: int | None = None
    plan_hash_value: str | None = None
    collected_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- DB Monitor Dashboard Summary ---

class DbMonitorSummary(BaseModel):
    total_instances: int = 0
    up_instances: int = 0
    down_instances: int = 0
    degraded_instances: int = 0
    total_active_sessions: int = 0
    total_tablespace_warnings: int = 0


# --- Cross-instance items for dashboard widgets ---

class TablespaceWarningItem(BaseModel):
    db_instance_id: int
    instance_name: str
    tablespace_name: str
    used_percent: float
    used_mb: float | None = None
    total_mb: float | None = None
    autoextensible: str | None = None

    model_config = {"from_attributes": True}


class CrossInstanceSlowQuery(BaseModel):
    db_instance_id: int
    instance_name: str
    sql_id: str | None = None
    sql_text: str | None = None
    username: str | None = None
    elapsed_seconds: float | None = None
    cpu_seconds: float | None = None
    buffer_gets: int | None = None
    executions: int | None = None

    model_config = {"from_attributes": True}


class BlockingSessionItem(BaseModel):
    db_instance_id: int
    instance_name: str
    sid: int | None = None
    serial_no: int | None = None
    username: str | None = None
    program: str | None = None
    status: str | None = None
    blocking_session: int | None = None
    wait_event: str | None = None
    seconds_in_wait: float | None = None
    sql_text: str | None = None

    model_config = {"from_attributes": True}


class DbDashboardDetails(BaseModel):
    tablespace_warnings: list[TablespaceWarningItem] = []
    top_slow_queries: list[CrossInstanceSlowQuery] = []
    blocking_sessions: list[BlockingSessionItem] = []


# --- Agent Ingest Payload ---

class DbAgentTablespace(BaseModel):
    tablespace_name: str
    total_mb: float | None = None
    used_mb: float | None = None
    free_mb: float | None = None
    used_percent: float | None = None
    autoextensible: str | None = None
    max_mb: float | None = None
    status: str | None = None


class DbAgentSession(BaseModel):
    sid: int | None = None
    serial_no: int | None = None
    username: str | None = None
    program: str | None = None
    machine: str | None = None
    status: str | None = None
    sql_id: str | None = None
    sql_text: str | None = None
    wait_class: str | None = None
    wait_event: str | None = None
    seconds_in_wait: float | None = None
    blocking_session: int | None = None
    logon_time: datetime | None = None
    elapsed_seconds: float | None = None


class DbAgentSlowQuery(BaseModel):
    sql_id: str | None = None
    sql_text: str | None = None
    username: str | None = None
    elapsed_seconds: float | None = None
    cpu_seconds: float | None = None
    buffer_gets: int | None = None
    disk_reads: int | None = None
    rows_processed: int | None = None
    executions: int | None = None
    plan_hash_value: str | None = None


class DbAgentPerformance(BaseModel):
    buffer_cache_hit_ratio: float | None = None
    library_cache_hit_ratio: float | None = None
    parse_count_total: int | None = None
    hard_parse_count: int | None = None
    execute_count: int | None = None
    user_commits: int | None = None
    user_rollbacks: int | None = None
    physical_reads: int | None = None
    physical_writes: int | None = None
    redo_size: int | None = None
    sga_total_mb: float | None = None
    pga_total_mb: float | None = None
    active_sessions: int | None = None
    inactive_sessions: int | None = None
    total_sessions: int | None = None
    max_sessions: int | None = None
    db_uptime_seconds: int | None = None


class DbAgentMetricsPayload(BaseModel):
    instance_name: str
    db_type: str = "oracle"
    host: str | None = None
    port: int | None = None
    service_name: str | None = None
    environment: str | None = None
    tablespaces: list[DbAgentTablespace] = []
    sessions: list[DbAgentSession] = []
    slow_queries: list[DbAgentSlowQuery] = []
    performance: DbAgentPerformance | None = None
    collected_at: datetime | None = None


class DbAgentMetricsResponse(BaseModel):
    success: bool
    message: str
    db_instance_id: int | None = None


# Fix forward references
DbInstanceDetail.model_rebuild()
