// 시계 갱신
function startClock() {
  const dateEl = document.getElementById("clockDate");
  const timeEl = document.getElementById("clockTime");
  const weekdays = [
    "일요일",
    "월요일",
    "수요일",
    "수요일",
    "목요일",
    "금요일",
    "토요일"
  ];

  function pad2(n) {
    return String(n).padStart(2, "0");
  }

  function tick() {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = pad2(now.getMonth() + 1);
    const dd = pad2(now.getDate());
    const dayName = weekdays[now.getDay()];
    const hh = pad2(now.getHours());
    const mi = pad2(now.getMinutes());
    const ss = pad2(now.getSeconds());

    dateEl.textContent = `${yyyy}-${mm}-${dd} (${dayName})`;
    timeEl.textContent = `${hh}:${mi}:${ss}`;
  }

  tick();
  setInterval(tick, 1000);
}

// 키패드 입력 처리
function initKeypad() {
  const idValueEl = document.getElementById("idValue");
  const keypadButtons = document.querySelectorAll(".key-btn[data-key]");
  const clearBtn = document.querySelector(".key-btn[data-action='clear']");
  const submitBtn = document.getElementById("submitBtn");

  let currentValue = "";

  function renderValue() {
    if (!currentValue) {
      idValueEl.textContent = "ID";
      idValueEl.classList.add("placeholder");
    } else {
      idValueEl.textContent = currentValue;
      idValueEl.classList.remove("placeholder");
    }
  }

  keypadButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.getAttribute("data-key");
      if (currentValue.length >= 12) return;
      currentValue += key;
      renderValue();
    });
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      currentValue = "";
      renderValue();
    });
  }

  if (submitBtn) {
    submitBtn.addEventListener("click", async() => {
      const trimmed = currentValue.trim();
      if (!trimmed) {
        alert("아이디를 먼저 입력해 주세요.");
        return;
      }

      // 아이디 존재 시 POST 요청
      try {
      const resp = await fetch("/attendance", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          kioskId: trimmed,
          // 필요하면 추가 필드
          // timestamp: new Date().toISOString()
        })
      });

      if (!resp.ok) {
        throw new Error("서버 오류: " + resp.status);
      }

      const data = await resp.json();
      // 예: { status: "ok", message: "..." } 형식이라고 가정
      
      // 성공 후 입력 초기화
      currentValue = "";
      renderValue();
      
      showAttendanceModal(data.message, trimmed);

    } catch (e) {
      console.error(e);
      alert("등록되지 않은 ID입니다");
    }
    });
  }

  renderValue();
}

function showAttendanceModal(message, id) {
  const overlay = document.getElementById("attendModal");
  const msgEl = document.getElementById("attendModalMessage");
  const closeBtn = document.getElementById("modalCloseBtn");
  const logBtn = document.getElementById("modalLogBtn");

  if (!overlay || !msgEl) return;

  msgEl.textContent = message;
  overlay.classList.add("active");

  // 닫기 버튼
  if (closeBtn) {
    closeBtn.onclick = () => {
      overlay.classList.remove("active");
    };
  }

  // 출석 기록 보기 버튼
  if (logBtn) {
    logBtn.onclick = () => {
      // 로그 페이지 URL에 맞게 변경
      window.location.href = "/logview?id="+id;
    };
  }

  // 배경 클릭 시 닫기 (선택)
  const backdrop = overlay.querySelector(".modal-backdrop");
  if (backdrop) {
    backdrop.onclick = () => {
      overlay.classList.remove("active");
    };
  }
}


document.addEventListener("DOMContentLoaded", () => {
  startClock();
  initKeypad();
});
