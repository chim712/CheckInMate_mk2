// 시계 갱신
function startClock() {
  const dateEl = document.getElementById("clockDate");
  const timeEl = document.getElementById("clockTime");
  const weekdays = [
    "일요일",
    "월요일",
    "화요일",
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
          source: "KIOSK",
          meta: { userAgent: navigator.userAgent }
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
  const checkoutBtn = document.getElementById("modalCheckoutBtn");

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

// 퇴근처리 버튼
if (checkoutBtn) {
  checkoutBtn.onclick = async () => {
    try {
      checkoutBtn.disabled = true;

      // 필요 시 meta에 추가 정보 넣기(예: 브라우저/화면/시간 등)
      const payload = {
        kioskId: id,
        source: "KIOSK", // 백엔드에서 기본값도 KIOSK지만 명시적으로 보냄
        meta: {
          // 프로젝트에서 유용한 메타만 남기는 편이 좋음
          userAgent: navigator.userAgent,
          // timestamp: new Date().toISOString(), // 필요하면 사용
        },
      };

      // 엔드포인트는 실제 라우팅에 맞춰야 함.
      // FastAPI에서 end_attendance가 /attendance/end 라우트라면 그에 맞게 변경.
      const resp = await fetch("/attendance/end", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) {
        let detail = "";
        try {
          const err = await resp.json();
          // FastAPI 기본 에러 포맷 대응
          detail =
            err?.detail
              ? (typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail))
              : JSON.stringify(err);
        } catch (_) {
          detail = await resp.text().catch(() => "");
        }
        throw new Error(`서버 오류: ${resp.status}${detail ? ` - ${detail}` : ""}`);
      }

      const data = await resp.json();
      // data 예: { memberId, name, eventType:"END", status:"INACTIVE" }

      // idempotent라서 이미 INACTIVE여도 같은 성공 응답이 올 수 있음
      const nameText = data?.name ? `(${data.name}) ` : "";
      alert("퇴근 처리 되었습니다! 오늘도 행복한 하루 되세요.");

      overlay.classList.remove("active");
    } catch (e) {
      console.error(e);
      alert("퇴근 처리에 실패했습니다.");
    } finally {
      checkoutBtn.disabled = false;
    }
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
