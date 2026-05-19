const searchForm = document.querySelector("#searchForm");
const firstNameInput = document.querySelector("#firstNameInput");
const lastNameInput = document.querySelector("#lastNameInput");
const personalIdInput = document.querySelector("#personalIdInput");
const birthYearInput = document.querySelector("#birthYearInput");
const addressInput = document.querySelector("#addressInput");
const clearButton = document.querySelector("#clearButton");
const notice = document.querySelector("#notice");
const thead = document.querySelector("#dataTable thead");
const tbody = document.querySelector("#dataTable tbody");
const emptyState = document.querySelector("#emptyState");
const rowCount = document.querySelector("#rowCount");
const shownCount = document.querySelector("#shownCount");
const columnCount = document.querySelector("#columnCount");

const inputs = [firstNameInput, lastNameInput, personalIdInput, birthYearInput, addressInput];

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function runSearch() {
  const params = new URLSearchParams({
    first_name: firstNameInput.value.trim(),
    last_name: lastNameInput.value.trim(),
    personal_id: personalIdInput.value.trim(),
    birth_year: birthYearInput.value.trim(),
    address: addressInput.value.trim()
  });
  const hasFilters = inputs.some((input) => input.value.trim());
  const response = await fetch(`/api/search?${params.toString()}`);
  const data = await response.json();

  if (!data.ok) {
    notice.classList.remove("ok");
    notice.innerHTML = `<strong>ბაზა ვერ მოიძებნა.</strong> ${escapeHtml(data.error)}`;
    return;
  }

  notice.classList.add("ok");
  notice.innerHTML = hasFilters
    ? `<strong>ძიება შესრულდა.</strong> პირობები ერთმანეთთან დაკავშირებულია; ნაჩვენებია პირველი ${data.rows.length} შედეგი.`
    : `<strong>ბაზა მზადაა.</strong> შეავსეთ ერთი ან რამდენიმე ველი და დააჭირეთ ძებნას.`;

  rowCount.textContent = data.total.toLocaleString("ka-GE");
  shownCount.textContent = data.matched.toLocaleString("ka-GE");
  columnCount.textContent = data.columns.length.toLocaleString("ka-GE");
  emptyState.classList.toggle("hidden", data.rows.length > 0);

  thead.innerHTML = data.columns.length
    ? `<tr>${data.columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>`
    : "";

  tbody.innerHTML = data.rows.map((row) =>
    `<tr>${data.columns.map((column) => `<td>${escapeHtml(row[column])}</td>`).join("")}</tr>`
  ).join("");
}

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  runSearch();
});

clearButton.addEventListener("click", () => {
  inputs.forEach((input) => {
    input.value = "";
  });
  runSearch();
  firstNameInput.focus();
});

runSearch();
