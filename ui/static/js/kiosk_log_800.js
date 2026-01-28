const weekdayMap = {
  mon: "월요일",
  tue: "화요일",
  wed: "수요일",
  thu: "목요일",
  fri: "금요일",
  sat: "토요일",
  sun: "일요일",
};

// ====== 설정 ======
const WEEKLY_GOAL_HOURS = 30; // 목표 시간(필요하면 바꾸세요)

function prettyKoreanName(name) {
  return (name || "").split("").join(" ");
}

// YYYY-MM-DD (local)
function toISODateLocal(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

// URL 쿼리에서 kioskId 읽기 (?id=1129)
function getKioskIdFromQuery() {
  const url = new URL(window.location.href);
  return url.searchParams.get("id");
}

// ====== 날짜/주 계산 ======
function getMondayISO(d = new Date()) {
  const dd = new Date(d);
  const day = dd.getDay(); // 0 Sun
  const diff = (day === 0 ? -6 : 1 - day); // Monday start
  dd.setDate(dd.getDate() + diff);
  return toISODateLocal(dd);
}

function addDaysISO(iso, n) {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + n);
  return toISODateLocal(d);
}

function setTodayHeader(entryOrNull) {
  const todayISO = toISODateLocal();
  const dateEl = document.getElementById("todayDate");
  const weekdayEl = document.getElementById("todayWeekday");

  dateEl.textContent = entryOrNull?.date || todayISO;

  const dayCode = (entryOrNull?.day || "").toLowerCase();
  if (weekdayMap[dayCode]) {
    weekdayEl.textContent = weekdayMap[dayCode];
  } else {
    // fallback: JS로 요일 계산
    const d = new Date(`${todayISO}T00:00:00`);
    const jsDay = d.getDay(); // 0 Sun
    const map = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"];
    weekdayEl.textContent = map[jsDay] || "";
  }
}

// ====== 이벤트/세션 누적 계산 (핵심) ======
function parseHHMMSS_toSec(t) {
  if (!t) return null;
  const [hh, mm, ss] = String(t).split(":").map(Number);
  if ([hh, mm, ss].some(n => Number.isNaN(n))) return null;
  return hh * 3600 + mm * 60 + ss;
}

/**
 * 하루 events로부터 "start ~ 마지막 extend(or end)"를 세션 단위로 누적합 한다.
 * - start 나오면 세션 시작
 * - extend/end는 lastActive 갱신
 * - 다음 start 나오면 이전 세션을 닫고 누적
 * - 마지막도 닫고 누적
 */
function calcDayDurationSeconds(events) {
  if (!Array.isArray(events) || events.length === 0) return 0;

  // 방어적 정렬 (서버가 보장해도 OK)
  const evs = [...events].sort((a, b) => String(a.time).localeCompare(String(b.time)));

  let total = 0;
  let startAt = null;     // seconds
  let lastActive = null;  // seconds

  const closeSession = () => {
    if (startAt != null && lastActive != null && lastActive >= startAt) {
      total += (lastActive - startAt);
    }
    startAt = null;
    lastActive = null;
  };

  for (const ev of evs) {
    const type = (ev.type || "").toLowerCase();
    const sec = parseHHMMSS_toSec(ev.time);
    if (sec == null) continue;

    if (type === "start") {
      // 새 start는 이전 세션을 마감하고 새 세션 시작
      closeSession();
      startAt = sec;
      lastActive = null;
      continue;
    }

    if (type === "extend" || type === "end") {
      if (startAt != null) lastActive = sec;
      continue;
    }

    // 기타 타입은 일단 무시
  }

  closeSession();
  return total;
}

function secondsToHM(totalSec) {
  const totalMinutes = Math.floor(totalSec / 60);
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  return { totalMinutes, h, m };
}

function computeWeekSummaryFromLogData(logData, goalHours = WEEKLY_GOAL_HOURS) {
  const mon = getMondayISO(new Date());
  const sun = addDaysISO(mon, 6);

  let totalSec = 0;
  let daysPresent = 0;

  for (const entry of (logData || [])) {
    if (!entry?.date) continue;
    if (entry.date < mon || entry.date > sun) continue;

    const sec = calcDayDurationSeconds(entry.events || []);
    totalSec += sec;
    if (sec > 0) daysPresent += 1;
  }

  const { totalMinutes, h, m } = secondsToHM(totalSec);

  return {
    totalMinutes,
    goalHours,
    weekStart: mon,
    weekEnd: sun,
    daysPresent,
    _h: h, // 내부 편의(표시용)
    _m: m,
  };
}

// 당일 출석 시간 및 현재 세션 누적 시간
function calcDurationSec(events) {
  let total = 0;
  let start = null;

  for (const ev of events) {
    const t = ev.type;
    const sec = parseHHMMSS_toSec(ev.time);
    if (sec == null) continue;

    if (t === "start") {
      start = sec;
    } else if ((t === "extend" || t === "end") && start != null) {
      total = sec - start;
    }
  }
  return total;
}

function formatHM(sec) {
  const m = Math.floor(sec / 60);
  const h = Math.floor(m / 60);
  return `${h}시간 ${m % 60}분`;
}



// 도넛이 HTML/CSS에 있으면 자동 반영 (없으면 조용히 무시)
function setDonutPercent(pct) {
  const donut = document.getElementById("donut");
  const donutPct = document.getElementById("donutPct");
  if (!donut || !donutPct) return;

  const p = Math.max(0, Math.min(100, Math.round(pct)));
  donutPct.textContent = `${p}%`;

  const deg = (p / 100) * 360;
  // 색상은 CSS에 맞춰 수정 가능
  donut.style.background = `conic-gradient(#2563eb ${deg}deg, #e5e7eb 0deg)`;
}

// ====== UI 렌더 ======
function badgeClass(typeRaw) {
  const t = (typeRaw || "").toLowerCase();
  if (t === "start") return "badge start";
  if (t === "extend") return "badge extend";
  if (t === "end") return "badge end";
  return "badge";
}

function renderToday(entryOrNull, kioskId) {
  const listEl = document.getElementById("todayList");
  listEl.innerHTML = "";

  const todayTotalEl = document.getElementById("todayTotal");
  const sessionTotalEl = document.getElementById("sessionTotal");

  if (!entryOrNull || !entryOrNull.events?.length) {
    todayTotalEl.textContent = "오늘 합계 -";
    sessionTotalEl.textContent = "이번 세션 -";
  } else {
    const events = entryOrNull.events;

    // 오늘 전체 누적
    const todaySec = calcDayDurationSeconds(events);
    todayTotalEl.textContent = `오늘 합계 ${formatHM(todaySec)}`;

    // 이번 세션: 마지막 start 기준
    const sessionSec = calcDurationSec(events);
    sessionTotalEl.textContent = `이번 세션 ${formatHM(sessionSec)}`;
  }

  const events = (entryOrNull?.events || [])
  .slice()
  .sort((a, b) => String(b.time || "").localeCompare(String(a.time || "")));
  if (!events.length) {
    const box = document.createElement("div");
    box.className = "empty-note";
    box.innerHTML = `
      <div>오늘 기록이 없습니다.</div>
      <div>과거 기록은 QR로 확인하세요.</div>
    `;
    listEl.appendChild(box);
    return;
  }

  // Bullet 유지
  events.forEach((ev) => {
    const row = document.createElement("div");
    row.className = "bullet";

    const time = document.createElement("div");
    time.className = "b-time";
    time.textContent = ev.time || "";

    const mid = document.createElement("div");
    mid.className = "b-mid";
    // 서버가 확정 기기명 내려준다는 전제: source 사용
    const src = ev.source ? `${ev.source}` : "";
    mid.textContent = src || "";

    const badge = document.createElement("div");
    badge.className = badgeClass(ev.type);
    badge.textContent = (ev.type || "").toLowerCase() || "-";

    row.appendChild(time);
    row.appendChild(mid);
    row.appendChild(badge);
    listEl.appendChild(row);
  });
}

function renderLeft(data, kioskId) {
  const userName = data.userName || "";
  document.getElementById("userName").textContent = prettyKoreanName(userName);

  // QR: 고정 URL 우선
  const base = window.location.origin;
  const url = `https://attendance.imagine.io.kr/`;
  const qrUrlEl = document.getElementById("qrUrlText");
  if (qrUrlEl) qrUrlEl.textContent = url;

  const weeklyBody = document.getElementById("weeklyBody");
  const weeklyEmpty = document.getElementById("weeklyEmpty");

  // 1) 서버 weekSummary가 있으면 사용
  // 2) 없으면 logData로 계산
  const logData = data.logData || [];
  let ws = data.weekSummary;

  if (!ws || typeof ws.totalMinutes !== "number") {
    ws = computeWeekSummaryFromLogData(logData, WEEKLY_GOAL_HOURS);
  }

  if (ws && typeof ws.totalMinutes === "number") {
    weeklyEmpty.hidden = true;
    weeklyBody.hidden = false;

    const h = Math.floor(ws.totalMinutes / 60);
    const m = ws.totalMinutes % 60;
    const timeEl = document.getElementById("weeklyTime");
    if (timeEl) timeEl.textContent = `${h}시간 ${m}분`;

    const goalHours = (typeof ws.goalHours === "number") ? ws.goalHours : WEEKLY_GOAL_HOURS;
    const goalEl = document.getElementById("weeklyGoal");
    if (goalEl) goalEl.textContent = `(목표 ${goalHours}시간)`;

    const range = (ws.weekStart && ws.weekEnd) ? `${ws.weekStart} ~ ${ws.weekEnd}` : "-";
    const rangeEl = document.getElementById("weeklyRange");
    if (rangeEl) rangeEl.textContent = `기간: ${range}`;

    const days = (typeof ws.daysPresent === "number") ? `${ws.daysPresent}일` : "-";
    const daysEl = document.getElementById("weeklyDays");
    if (daysEl) daysEl.textContent = `이번 주 출근일: ${days}`;

    // 도넛 퍼센트 반영(도넛 DOM이 있으면)
    const goalMin = goalHours * 60;
    const pct = goalMin > 0 ? (ws.totalMinutes / goalMin) * 100 : 0;
    setDonutPercent(pct);
  } else {
    weeklyBody.hidden = true;
    weeklyEmpty.hidden = false;
    setDonutPercent(0);
  }
}

async function loadAttendance() {
  const kioskId = getKioskIdFromQuery();

  try {
    const res = await fetch(`/attendance/logs?kioskId=${encodeURIComponent(kioskId)}`);
    if (!res.ok) throw new Error(`API 오류: ${res.status}`);

    const data = await res.json();

    // 좌측 렌더
    renderLeft(data, kioskId);

    // 우측: 당일만
    const todayISO = toISODateLocal();
    const logData = data.logData || [];
    const todayEntry = logData.find(e => e.date === todayISO) || null;

    setTodayHeader(todayEntry);
    renderToday(todayEntry, kioskId);

  } catch (err) {
    console.error(err);

    document.getElementById("userName").textContent = "-";
    document.getElementById("todayDate").textContent = toISODateLocal();
    document.getElementById("todayWeekday").textContent = "";

    const listEl = document.getElementById("todayList");
    listEl.innerHTML = "";
    const box = document.createElement("div");
    box.className = "empty-note";
    box.innerHTML = `
      <div>출석 기록을 불러오지 못했습니다.</div>
      <div>네트워크/서버 상태를 확인하세요.</div>
    `;
    listEl.appendChild(box);

    // 도넛 있으면 0으로
    setDonutPercent(0);

    // 주간 영역은 안내
    const weeklyBody = document.getElementById("weeklyBody");
    const weeklyEmpty = document.getElementById("weeklyEmpty");
    if (weeklyBody && weeklyEmpty) {
      weeklyBody.hidden = true;
      weeklyEmpty.hidden = false;
    }
  }
}

function enableDragScroll(el) {
  let isDown = false;
  let startY = 0;
  let startScrollTop = 0;

  // 터치(모바일/패널) 우선
  el.addEventListener("touchstart", (e) => {
    if (!e.touches || e.touches.length !== 1) return;
    isDown = true;
    startY = e.touches[0].clientY;
    startScrollTop = el.scrollTop;
  }, { passive: true });

  el.addEventListener("touchmove", (e) => {
    if (!isDown || !e.touches || e.touches.length !== 1) return;
    const y = e.touches[0].clientY;
    const dy = y - startY;
    el.scrollTop = startScrollTop - dy;
  }, { passive: true });

  el.addEventListener("touchend", () => {
    isDown = false;
  });

  // 마우스 드래그(터치가 마우스로 들어오는 환경 대응)
  el.addEventListener("mousedown", (e) => {
    isDown = true;
    startY = e.clientY;
    startScrollTop = el.scrollTop;
    el.classList.add("dragging");
    e.preventDefault(); // 텍스트 드래그 방지
  });

  window.addEventListener("mousemove", (e) => {
    if (!isDown) return;
    const dy = e.clientY - startY;
    el.scrollTop = startScrollTop - dy;
  });

  window.addEventListener("mouseup", () => {
    if (!isDown) return;
    isDown = false;
    el.classList.remove("dragging");
  });
}


document.addEventListener("DOMContentLoaded", loadAttendance);

document.addEventListener("DOMContentLoaded", () => {
  loadAttendance();
  const scroller = document.getElementById("todayList");
  if (scroller) enableDragScroll(scroller);
});
