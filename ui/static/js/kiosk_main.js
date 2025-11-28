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
      idValueEl.textContent = "아이디를 입력하세요";
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
    submitBtn.addEventListener("click", () => {
      const trimmed = currentValue.trim();
      if (!trimmed) {
        alert("아이디를 먼저 입력해 주세요.");
        return;
      }
      console.log("등록 요청 ID:", trimmed);
      alert(`ID ${trimmed} 출석 등록 요청을 전송했습니다.`);
      currentValue = "";
      renderValue();
    });
  }

  renderValue();
}

document.addEventListener("DOMContentLoaded", () => {
  startClock();
  initKeypad();
});
