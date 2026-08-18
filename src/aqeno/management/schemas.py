from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aqeno.domain.access import AccessDecision, AccessSource, AudienceMode
from aqeno.domain.content import ContentKind
from aqeno.domain.profile import ExperienceLevel, Role


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorBody(ApiModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(ApiModel):
    error: ErrorBody


class AuthStatus(ApiModel):
    setup_required: bool
    authenticated: bool
    physical_confirmation_available: bool = True
    csrf_token: str | None = None


class PasswordRequest(ApiModel):
    password: str = Field(min_length=1, max_length=1024, json_schema_extra={"writeOnly": True})


class InitialPasswordRequest(ApiModel):
    confirmation_id: UUID
    password: str = Field(min_length=10, max_length=1024, json_schema_extra={"writeOnly": True})


class PasswordChangeRequest(ApiModel):
    current_password: str = Field(
        min_length=1, max_length=1024, json_schema_extra={"writeOnly": True}
    )
    new_password: str = Field(min_length=10, max_length=1024, json_schema_extra={"writeOnly": True})


class ConfirmationResponse(ApiModel):
    id: UUID
    purpose: Literal["setup", "recovery"]
    state: Literal["pending", "confirmed"]
    expires_in_seconds: int


class SessionResponse(ApiModel):
    csrf_token: str
    expires_in_seconds: int


class DeviceStatus(ApiModel):
    device_id: UUID
    name: str
    aqeno_version: str
    readiness: str
    database_health: str
    management_api: str = "ready"
    local_only: bool = True
    capabilities: list[str]
    storage_total_bytes: int
    storage_free_bytes: int


class DiagnosticsStatus(ApiModel):
    functional: bool
    readiness: str
    database: str
    storage_writable: bool
    audio: str
    display: str
    nfc: str
    physical_controls: str
    last_playback_error: str | None = None


class Chapter(ApiModel):
    id: str
    index: int
    title: str | None
    start_seconds: float
    duration_seconds: float | None


class SourceSummary(ApiModel):
    type: Literal["local_file", "http"]
    location: Literal["internal", "mounted_external", "remote"]
    display_name: str
    seekable: bool


class MediaSummary(ApiModel):
    id: UUID
    title: str
    kind: ContentKind
    available: bool
    duration_seconds: float | None
    language: str | None
    artwork_thumbnail_url: str | None


class MediaDetail(MediaSummary):
    chapters: list[Chapter]
    sources: list[SourceSummary]
    artwork_url: str | None
    kind_overridden: bool
    last_seen: float | None
    resume_seconds: float | None = None


class MediaPage(ApiModel):
    items: list[MediaSummary]
    next_cursor: str | None
    total: int


class MediaPatch(ApiModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    kind: ContentKind | None = None
    language: str | None = Field(default=None, min_length=2, max_length=16)


class OperationResponse(ApiModel):
    id: UUID
    type: str
    state: str
    progress: int = Field(ge=0, le=100)
    result: dict[str, Any] | None = None
    error: ErrorBody | None = None


class TokenResource(ApiModel):
    uid: str
    assigned_media_id: UUID | None


class TokenCaptureResponse(ApiModel):
    id: UUID
    state: str
    token_uid: str | None
    assigned_media_id: UUID | None


class TokenAssignmentRequest(ApiModel):
    media_id: UUID


class PlaybackStatus(ApiModel):
    state: str
    media_id: UUID | None
    title: str | None
    chapter_title: str | None
    position_seconds: float | None
    duration_seconds: float | None
    volume: int | None
    failure_code: str | None


class DisplaySettings(ApiModel):
    kids_early: int
    kids_reader: int
    kids_explorer: int
    easy: int
    standard: int
    night_override: int
    dim_hold_kids_early: int
    dim_hold_standard: int
    setup_idle: int
    setup_idle_night: int


class BrightnessSettings(ApiModel):
    interactive_kids_early: int
    interactive_other_kids: int
    interactive_easy: int
    interactive_standard: int
    dim_kids_early: int
    dim_standard: int
    ambient_kids_early: int
    ambient_other_kids: int
    ambient_easy: int
    ambient_standard: int
    night_minimum: int
    led_normal: int


class VolumeSettings(ApiModel):
    child_maximum: int
    night_ceiling: int
    headphone_maximum: int
    easy_standard_maximum: int
    encoder_step: int
    first_boot: int


class NfcSettings(ApiModel):
    debounce_ms: int
    ack_tone_unassigned: bool


class ResumeSettings(ApiModel):
    rewind_seconds: int


class SleepTimerSettings(ApiModel):
    duration_minutes: int
    presets_minutes: list[int]
    fade_out_seconds: int
    action_at_end: Literal["pause", "stop"]


class LibrarySettings(ApiModel):
    roots: list[str] = Field(min_length=1, max_length=8)
    scan_on_startup: bool
    follow_symlinks: bool


class SettingsResource(ApiModel):
    display: DisplaySettings
    brightness: BrightnessSettings
    volume: VolumeSettings
    resume: ResumeSettings
    sleep_timer: SleepTimerSettings
    nfc: NfcSettings
    library: LibrarySettings
    language: Literal["de", "en"]
    apply_mode: Literal["restart_required"] = "restart_required"


class ControlCapabilityResource(ApiModel):
    id: str
    type: Literal["button", "rotary_encoder"]
    label: str
    events: list[str]
    illumination: bool


class ControlActionResource(ApiModel):
    id: str
    label: str
    category: str
    compatible_events: list[str]


class ControlBindingResource(ApiModel):
    control_id: str
    event: str
    action_id: str | None
    supported: bool


class ControlsResource(ApiModel):
    controls: list[ControlCapabilityResource]
    actions: list[ControlActionResource]
    mappings: list[ControlBindingResource]
    illumination: Literal["off", "subtle", "clear"]


class ControlBindingPatch(ApiModel):
    action_id: str | None


class IlluminationPatch(ApiModel):
    illumination: Literal["off", "subtle", "clear"]


class ProfileDisplay(ApiModel):
    inactivity_timeout_seconds: int = Field(ge=5, le=900)
    night_timeout_seconds: int = Field(ge=5, le=30)
    allows_dim: bool
    dim_hold_seconds: int | None = Field(default=None, ge=5, le=60)
    interactive_brightness: int = Field(ge=0, le=100)
    dim_brightness: int = Field(ge=0, le=100)
    ambient_brightness: int = Field(ge=0, le=100)
    night_brightness: int = Field(ge=0, le=100)
    led_brightness: int = Field(ge=0, le=100)


class ProfileVolume(ApiModel):
    maximum: int = Field(ge=0, le=100)
    night_maximum: int = Field(ge=0, le=100)
    headphone_maximum: int = Field(ge=0, le=100)


class ProfileResource(ApiModel):
    name: str = Field(min_length=1, max_length=80)
    level: ExperienceLevel
    role: Role
    display: ProfileDisplay
    volume: ProfileVolume
    ambient_enabled: bool
    apply_mode: Literal["restart_required"] = "restart_required"


class FavoriteResource(ApiModel):
    profile_name: str
    media_id: UUID
    favorite: bool


class ProgressResource(ApiModel):
    profile_name: str
    media_id: UUID
    position_seconds: float | None


class AudienceResource(ApiModel):
    mode: AudienceMode
    profile_names: list[str] = Field(default_factory=list)


class BulkAccessRequest(ApiModel):
    media_ids: list[UUID] = Field(min_length=1, max_length=1000)
    operation: Literal["set_shared", "set_selected_profiles", "allow", "deny", "clear_override"]
    profile_names: list[str] = Field(default_factory=list, max_length=50)


class BulkAccessResult(ApiModel):
    media_count: int
    profile_count: int
    operation: str


class EffectiveAccessResource(ApiModel):
    media_id: UUID
    profile_name: str
    allowed: bool
    source: AccessSource
    explicit_decision: AccessDecision | None
    inherited_collection_ids: list[UUID]
    media_audience: AudienceResource | None


class CollectionWrite(ApiModel):
    name: str = Field(min_length=1, max_length=200)
    media_ids: list[UUID] = Field(default_factory=list, max_length=1000)


class CollectionResource(CollectionWrite):
    id: UUID
    audience: AudienceResource | None


class MediaSourceResource(ApiModel):
    id: str
    kind: Literal["local", "mounted_external"]
    path: str
    available: bool
