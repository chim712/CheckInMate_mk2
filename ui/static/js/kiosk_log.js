const weekdayMap = {
  mon: "월요일",
  tue: "화요일",
  wed: "수요일",
  thu: "목요일",
  fri: "금요일",
  sat: "토요일",
  sun: "일요일"
};

/**
 * type과 마지막 여부에 따라 문구 생성
 * - 마지막 이벤트면 타입에 상관없이 "(마지막 세션)"만 붙인다.
 * - 마지막이 아닌 start만 "출석 (세션 시작)"으로 표시.
 */
function buildEventDescription(type, isLastEvent) {
  let base;
  switch (type) {
    case "start":
      base = "출석";
      break;
    case "extend":
      base = "연장";
      break;
    case "end":
      base = "퇴실";
      break;
    default:
      base = type;
  }

  if (isLastEvent) {
    return `${base} (마지막 세션)`;
  }

  if (type === "start") {
    return "출석 (세션 시작)";
  }

  return base;
}

// "홍길동" → "홍 길 동"
function prettyKoreanName(name) {
  return name.split("").join(" ");
}

function renderAttendance(data) {
  const userName = data.userName || "";
  const logData = data.logData || [];

  // 상단 이름 표시
  document.getElementById("userName").textContent = prettyKoreanName(userName);

  const logListEl = document.getElementById("logList");
  logListEl.innerHTML = "";

  // 기록 없을 때 안내 문구
  if (!logData.length) {
    const empty = document.createElement("div");
    empty.style.padding = "24px";
    empty.style.fontSize = "18px";
    empty.style.color = "#6b7280";
    empty.textContent = "출석 기록이 없습니다.";
    logListEl.appendChild(empty);
    return;
  }

  logData.forEach(entry => {
    const [year, monthStr, dayStr] = (entry.date || "").split("-");
    const month = Number(monthStr || 0);
    const day = Number(dayStr || 0);

    const dayCode = (entry.day || "").toLowerCase();
    const weekday = weekdayMap[dayCode] || entry.day || "";

    const events = entry.events || [];
    if (!events.length) return;

    const lastIndex = events.length - 1;

    const card = document.createElement("div");
    card.className = "log-card";

    if (dayCode === "sat") {
      card.classList.add("weekend-sat");
    } else if (dayCode === "sun") {
      card.classList.add("weekend-sun");
    }

    const dateBox = document.createElement("div");
    dateBox.className = "date-box";

    const monthEl = document.createElement("div");
    monthEl.className = "date-month";
    monthEl.textContent = month ? `${month}월` : "";

    const dayEl = document.createElement("div");
    dayEl.className = "date-day";
    dayEl.textContent = day ? String(day) : "";

    const weekdayEl = document.createElement("div");
    weekdayEl.className = "date-weekday";
    weekdayEl.textContent = weekday;

    dateBox.appendChild(monthEl);
    dateBox.appendChild(dayEl);
    dateBox.appendChild(weekdayEl);

    const eventList = document.createElement("div");
    eventList.className = "event-list";

    events.forEach((ev, idx) => {
      const row = document.createElement("div");
      row.className = "event-row";

      const timeEl = document.createElement("div");
      timeEl.className = "event-time";
      timeEl.textContent = ev.time || "";

      const descEl = document.createElement("div");
      descEl.className = "event-desc";
      descEl.textContent = buildEventDescription(
        ev.type,
        idx === lastIndex
      );

      row.appendChild(timeEl);
      row.appendChild(descEl);
      eventList.appendChild(row);
    });

    card.appendChild(dateBox);
    card.appendChild(eventList);
    logListEl.appendChild(card);
  });
}

// URL 쿼리에서 kioskId 읽기 (?id=1129)
function getKioskIdFromQuery() {
  const url = new URL(window.location.href);
  const val = url.searchParams.get("id");
  return val;
}

// API 호출 → 데이터 로드
async function loadAttendance() {
  const kioskId = getKioskIdFromQuery();

  try {
    const res = await fetch(
      `http://127.0.0.1:8000/attendance/logs?kioskId=${encodeURIComponent(
        kioskId
      )}`
    );

    if (!res.ok) {
      throw new Error(`API 오류: ${res.status}`);
    }

    const data = await res.json();
    renderAttendance(data);
  } catch (err) {
    console.error(err);
    const logListEl = document.getElementById("logList");
    logListEl.innerHTML = "";
    const error = document.createElement("div");
    error.style.padding = "24px";
    error.style.fontSize = "18px";
    error.style.color = "#b91c1c";
    error.textContent = "출석 기록을 불러오지 못했습니다.";
    logListEl.appendChild(error);
  }
}

// 페이지 로드 시 자동 실행
document.addEventListener("DOMContentLoaded", () => {
  loadAttendance();
});
