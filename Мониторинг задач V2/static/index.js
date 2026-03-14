document.addEventListener("DOMContentLoaded", function () {
  // Элементы DOM
  const analyzeBtn = document.getElementById("analyzeBtn");
  const folderPathInput = document.getElementById("folderPath");
  const tableBody = document.getElementById("tableBody");
  const loadingDiv = document.getElementById("loading");
  const errorDiv = document.getElementById("error");
  const tableContainer = document.getElementById("tableContainer");
  const statsDiv = document.getElementById("stats");
  const suggestionsDiv = document.getElementById("suggestions");
  const filtersPanel = document.getElementById("filtersPanel");
  const groupingPanel = document.getElementById("groupingPanel");
  const applyFiltersBtn = document.getElementById("applyFiltersBtn");
  const resetFiltersBtn = document.getElementById("resetFiltersBtn");
  const groupBySelect = document.getElementById("groupBySelect");
  const exportBtn = document.getElementById("exportBtn");
  const modal = document.getElementById("taskModal");
  const modalBody = document.getElementById("modalBody");
  const closeBtn = document.querySelector(".close");
  const serchString = document.querySelector(".filter-input");

  // Переменные состояния
  let originalData = [];
  let filteredData = [];
  let currentSort = { column: "date", direction: "asc" };
  let filters = {
    date: "all",
    month: "all", // Добавьте эту строку
    br_status: "all",
    geo_status: "all",
    project_status: "all",
    drawing_status: "all",
    search: "",
  };
  // Хранилище заметок
  let taskNotes = JSON.parse(localStorage.getItem("taskNotes")) || {};

  // Инициализация
  analyzeBtn.addEventListener("click", function () {
    const path = folderPathInput.value.trim();
    analyzeFolder(path);
  });

  // Закрытие модального окна
  closeBtn.addEventListener("click", function () {
    modal.style.display = "none";
  });

  window.addEventListener("click", function (event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
  });

  // Обработчики фильтров
  applyFiltersBtn.addEventListener("click", applyFilters);

  serchString.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      applyFilters();
    }
  });
  resetFiltersBtn.addEventListener("click", resetFilters);
  groupBySelect.addEventListener("change", renderTable);
  exportBtn.addEventListener("click", exportToCSV);

  // Сортировка
  document.querySelectorAll(".sortable").forEach((header) => {
    header.addEventListener("click", function () {
      const column = this.dataset.sort;
      if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === "asc" ? "desc" : "asc";
      } else {
        currentSort.column = column;
        currentSort.direction = "asc";
      }
      renderTable();
    });
  });

  // ===== ДЕЛЕГИРОВАНИЕ СОБЫТИЙ ДЛЯ ЗАМЕТОК =====
  // Обработка ввода текста (показываем иконку сохранения)
  document.addEventListener("input", function (e) {
    if (e.target.classList.contains("note-input")) {
      const saveIcon = e.target.nextElementSibling;
      if (saveIcon && saveIcon.classList.contains("note-save-icon")) {
        saveIcon.style.display = "inline";
      }
    }
  });

  // Обработка потери фокуса (сохраняем заметку)
  document.addEventListener(
    "blur",
    function (e) {
      if (e.target.classList.contains("note-input")) {
        const taskNumber = e.target.dataset.task;
        const note = e.target.value;
        saveNote(taskNumber, note);

        const saveIcon = e.target.nextElementSibling;
        if (saveIcon && saveIcon.classList.contains("note-save-icon")) {
          saveIcon.style.display = "none";
        }
      }
    },
    true
  ); // Важно: используем capturing фазу для blur

  // Обработка нажатия Enter (сохраняем и убираем фокус)
  document.addEventListener("keypress", function (e) {
    if (e.key === "Enter" && e.target.classList.contains("note-input")) {
      e.target.blur(); // Это вызовет событие blur выше
    }
  });

  // Обработка клика по иконке сохранения (опционально)
  document.addEventListener("click", function (e) {
    // Клик по иконке сохранения
    if (e.target.classList.contains("fa-save") || e.target.classList.contains("note-save-icon")) {
      const icon = e.target.classList.contains("fa-save") ? e.target : e.target;
      const input = icon.previousElementSibling;
      if (input && input.classList.contains("note-input")) {
        saveNote(input.dataset.task, input.value);
        icon.style.display = "none";
      }
    }
  });

  // Основная функция анализа
  function analyzeFolder(path) {
    loadingDiv.style.display = "block";
    errorDiv.style.display = "none";
    tableContainer.style.display = "none";
    statsDiv.style.display = "none";
    filtersPanel.style.display = "none";
    groupingPanel.style.display = "none";
    suggestionsDiv.innerHTML = "";

    const url = path ? `/api/tasks?path=${encodeURIComponent(path)}` : "/api/tasks";

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        loadingDiv.style.display = "none";

        if (data.error) {
          showError(data.error, data.suggestions);
        } else {
          originalData = data;
          filteredData = [...data];
          updateFilters(data);
          updateStats(data);
          renderTable();

          filtersPanel.style.display = "block";
          groupingPanel.style.display = "block";
          statsDiv.style.display = "grid";
          tableContainer.style.display = "block";
        }
      })
      .catch((error) => {
        loadingDiv.style.display = "none";
        showError("Ошибка при загрузке данных: " + error.message);
      });
  }

  // Обновление фильтров
  function updateFilters(data) {
    // Сортируем даты правильно
    const dates = [...new Set(data.map((item) => item.date))].sort((a, b) => {
      const [dayA, monthA, yearA] = a.split(".").map(Number);
      const [dayB, monthB, yearB] = b.split(".").map(Number);
      return new Date(yearA, monthA - 1, dayA) - new Date(yearB, monthB - 1, dayB);
    });

    const dateFilter = document.getElementById("dateFilter");
    dateFilter.innerHTML = '<option value="all">Все даты</option>';
    dates.forEach((date) => {
      dateFilter.innerHTML += `<option value="${date}">${date}</option>`;
    });

    const months = [
      ...new Set(
        data.map((item) => {
          const month = parseInt(item.date.split(".")[1]);
          return month;
        })
      ),
    ].sort((a, b) => a - b);

    const monthFilter = document.getElementById("monthFilter");
    // Сохраняем текущее выбранное значение
    const currentMonthValue = monthFilter.value;
    monthFilter.innerHTML = '<option value="all">Все месяцы</option>';

    const monthNames = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"];

    months.forEach((month) => {
      if (!isNaN(month) && month >= 1 && month <= 12) {
        monthFilter.innerHTML += `<option value="${month}">${monthNames[month - 1]}</option>`;
      }
    });

    // Восстанавливаем выбранное значение, если оно существует в новых опциях
    if (currentMonthValue && months.includes(parseInt(currentMonthValue))) {
      monthFilter.value = currentMonthValue;
    }

    // Обновляем уникальные значения для других фильтров
    const geoStatuses = [...new Set(data.map((item) => item.geo_status))];
    const geoFilter = document.getElementById("geoStatusFilter");
    geoFilter.innerHTML = '<option value="all">Все</option>';
    geoStatuses.forEach((status) => {
      geoFilter.innerHTML += `<option value="${status}">${status}</option>`;
    });

    const projectStatuses = [...new Set(data.map((item) => item.project_status))];
    const projectFilter = document.getElementById("projectStatusFilter");
    projectFilter.innerHTML = '<option value="all">Все</option>';
    projectStatuses.forEach((status) => {
      projectFilter.innerHTML += `<option value="${status}">${status}</option>`;
    });

    const drawingStatuses = [...new Set(data.map((item) => item.drawing_status))];
    const drawingFilter = document.getElementById("drawingStatusFilter");
    drawingFilter.innerHTML = '<option value="all">Все</option>';
    drawingStatuses.forEach((status) => {
      drawingFilter.innerHTML += `<option value="${status}">${status}</option>`;
    });
  }

  // Применение фильтров
  function applyFilters() {
    filters = {
      date: document.getElementById("dateFilter").value,
      month: document.getElementById("monthFilter").value, // Добавьте эту строку
      br_status: document.getElementById("brStatusFilter").value,
      geo_status: document.getElementById("geoStatusFilter").value,
      project_status: document.getElementById("projectStatusFilter").value,
      drawing_status: document.getElementById("drawingStatusFilter").value,
      search: document.getElementById("searchInput").value.toLowerCase(),
    };

    filteredData = originalData.filter((item) => {
      // Фильтр по конкретной дате
      if (filters.date !== "all" && item.date !== filters.date) return false;

      // ДОБАВЬТЕ: Фильтр по месяцу
      if (filters.month !== "all") {
        const itemMonth = parseInt(item.date.split(".")[1]);
        if (itemMonth !== parseInt(filters.month)) return false;
      }

      // Остальные фильтры
      if (filters.br_status !== "all" && item.br_status !== filters.br_status) return false;
      if (filters.geo_status !== "all" && item.geo_status !== filters.geo_status) return false;
      if (filters.project_status !== "all" && item.project_status !== filters.project_status) return false;
      if (filters.drawing_status !== "all" && item.drawing_status !== filters.drawing_status) return false;
      if (filters.search && !item.task_number.toLowerCase().includes(filters.search)) return false;

      return true;
    });

    updateStats(filteredData);
    renderTable();
  }

  // Сброс фильтров
  function resetFilters() {
    document.getElementById("dateFilter").value = "all";
    document.getElementById("monthFilter").value = "all"; // Добавьте эту строку
    document.getElementById("brStatusFilter").value = "all";
    document.getElementById("geoStatusFilter").value = "all";
    document.getElementById("projectStatusFilter").value = "all";
    document.getElementById("drawingStatusFilter").value = "all";
    document.getElementById("searchInput").value = "";

    filteredData = [...originalData];
    updateStats(filteredData);
    renderTable();
  }

  // Обновление статистики
  function updateStats(data) {
    console.log("debug_1", data);
    document.getElementById("totalTasks").textContent = data.length;
    document.getElementById("brLoaded").textContent = data.filter((t) => t.br_status === "Загружено из БР").length;
    document.getElementById("geoWork").textContent = data.filter((t) => t.geo_status === "В работу").length;
    document.getElementById("drawingsReady").textContent = data.filter((t) => t.drawing_status && t.drawing_status.includes("Подготовлен")).length;
    document.getElementById("rejectCount").textContent = data.filter((t) => t.geo_status === "Отказ").length;
  }

  // Сортировка данных
  function sortData(data) {
    return data.sort((a, b) => {
      let valA = a[currentSort.column];
      let valB = b[currentSort.column];

      // Специальная обработка для дат
      if (currentSort.column === "date") {
        const [dayA, monthA, yearA] = valA.split(".").map(Number);
        const [dayB, monthB, yearB] = valB.split(".").map(Number);
        valA = new Date(yearA, monthA - 1, dayA);
        valB = new Date(yearB, monthB - 1, dayB);
      }

      if (valA < valB) return currentSort.direction === "asc" ? -1 : 1;
      if (valA > valB) return currentSort.direction === "asc" ? 1 : -1;
      return 0;
    });
  }

  // Группировка данных
  function groupData(data) {
    const groupBy = groupBySelect.value;
    if (groupBy === "none") return { groups: null, data: sortData(data) };

    const groups = {};
    data.forEach((item) => {
      let key;
      if (groupBy === "month") {
        // Извлекаем месяц из даты
        const month = item.date.split(".")[1];
        key = month ? getMonthName(parseInt(month)) : "Не указано";
      } else {
        key = item[groupBy] || "Не указано";
      }

      if (!groups[key]) groups[key] = [];
      groups[key].push(item);
    });

    return { groups, data: null };
  }

  // Получение названия месяца по номеру
  function getMonthName(monthNum) {
    const months = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"];
    return months[monthNum - 1] || monthNum;
  }

  // Рендер таблицы
  function renderTable() {
    const { groups, data } = groupData(filteredData);

    if (groups) {
      // Рендер с группировкой
      let html = "";

      // Сортируем группы (для месяцев - по номеру)
      const sortedGroups = Object.keys(groups).sort((a, b) => {
        if (groupBySelect.value === "month") {
          const monthOrder = {
            январь: 1,
            февраль: 2,
            март: 3,
            апрель: 4,
            май: 5,
            июнь: 6,
            июль: 7,
            август: 8,
            сентябрь: 9,
            октябрь: 10,
            ноябрь: 11,
            декабрь: 12,
          };
          return (monthOrder[a] || 0) - (monthOrder[b] || 0);
        }
        return a.localeCompare(b);
      });

      sortedGroups.forEach((groupKey) => {
        const groupItems = sortData(groups[groupKey]);

        // Заголовок группы
        html += `<tr class="group-header"><td colspan="9">
        <i class="fas fa-folder-open"></i> ${groupKey} (${groupItems.length})
     </td></tr>`;

        // Элементы группы
        groupItems.forEach((task) => {
          html += renderRow(task);
        });
      });

      tableBody.innerHTML = html;
    } else {
      // Рендер без группировки
      const sortedData = sortData(data);
      tableBody.innerHTML = sortedData.map((task) => renderRow(task)).join("");
    }

    // Добавляем обработчики для кнопок действий
    document.querySelectorAll(".action-btn.info").forEach((btn) => {
      btn.addEventListener("click", function () {
        const taskNumber = this.dataset.task;
        showTaskDetails(taskNumber);
      });
    });

    document.querySelectorAll(".action-btn.folder").forEach((btn) => {
      btn.addEventListener("click", function () {
        const folderPath = this.dataset.folder;
        openFolder(folderPath);
      });
    });
  }

  // Рендер одной строки
  // Рендер одной строки
  function renderRow(task) {
    const brClass = task.br_status === "Загружено из БР" ? "status-ok" : "status-bad";
    const geoClass = getGeoClass(task.geo_status);
    const projectClass = task.project_status && task.project_status.includes("Подготовлен") ? "status-ok" : "status-bad";
    const drawingClass = task.drawing_status && task.drawing_status.includes("Подготовлен") ? "status-ok" : "status-bad";
    const refClass = getReferenceClass(task.reference_status);
    const note = getNote(task.task_number);

    // Определяем класс подсветки для строки
    let highlightClass = "";
    if (task.geo_status === "В работу" && task.drawing_status === "Чертеж не подготовлен") {
      highlightClass = "highlight-both-critical"; // Оба условия
    } else if (task.geo_status === "В работу") {
      highlightClass = "highlight-geo-work";
    } else if (task.drawing_status === "Чертеж не подготовлен") {
      highlightClass = "highlight-drawing-not-ready";
    }

    return `
      <tr class="${highlightClass}">
          <td>${task.date}</td>
          <td class="task-number"><strong>${task.task_number}</strong></td>
          <td class="${brClass}">${task.br_status}</td>
          <td class="${geoClass}">${task.geo_status}</td>
          <td class="${projectClass}">${task.project_status}</td>
          <td class="${drawingClass}">${task.drawing_status}</td>
          <td class="${refClass}">${task.reference_status || "-"}</td>
          <td>
              <div class="note-cell">
                  <input type="text" 
                         class="note-input" 
                         value="${note.replace(/"/g, "&quot;")}" 
                         placeholder="Добавить примечание..."
                         data-task="${task.task_number}">
                  <i class="fas fa-save note-save-icon" style="display:none"></i>
              </div>
          </td>
          <td>
              <button class="action-btn info" data-task="${task.task_number}" title="Детали задачи">
                  <i class="fas fa-info-circle"></i>
              </button>
              <button class="action-btn folder" data-folder="${task.task_folder}" title="Открыть папку">
                  <i class="fas fa-folder-open"></i>
              </button>
          </td>
      </tr>
  `;
  }

  // Показать детали задачи
  function showTaskDetails(taskNumber) {
    const task = originalData.find((t) => t.task_number === taskNumber);
    if (!task) return;

    modalBody.innerHTML = `
              <p><strong>Дата:</strong> ${task.date}</p>
              <p><strong>Номер задачи:</strong> ${task.task_number}</p>
              <p><strong>Статус БР:</strong> <span class="status-ok">${task.br_status}</span></p>
              <p><strong>Геоанализ:</strong> <span class="${getGeoClass(task.geo_status)}">${task.geo_status}</span></p>
              <p><strong>Проект:</strong> <span class="${task.project_status && task.project_status.includes("Подготовлен") ? "status-ok" : "status-bad"}">${task.project_status}</span></p>
              <p><strong>Чертеж:</strong> <span class="${task.drawing_status && task.drawing_status.includes("Подготовлен") ? "status-ok" : "status-bad"}">${task.drawing_status}</span></p>
              <p><strong>Справка:</strong> <span class="${getReferenceClass(task.reference_status)}">${task.reference_status || "Не указано"}</span></p>
              <p><strong>Путь к папке:</strong> <small>${task.task_folder}</small></p>
          `;

    modal.style.display = "flex";
  }

  function openFolder(folderPath) {
    // Кодируем путь для URL
    const encodedPath = encodeURIComponent(folderPath);

    // Отправляем GET запрос
    fetch(`/api/open-folder?path=${encodedPath}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          console.log("✅ " + data.message);
        } else {
          console.log("❌ " + data.message);
        }
      })
      .catch((error) => {
        console.log("Ошибка: " + error);
      });
  }

  // Экспорт в CSV
  function exportToCSV() {
    const headers = ["Дата", "Номер задачи", "Статус БР", "Геоанализ", "Проект", "Чертеж", "Справка", "Примечание", "Путь к папке"];
    const csvData = filteredData.map((task) => [task.date, task.task_number, task.br_status, task.geo_status, task.project_status, task.drawing_status, task.reference_status || "", getNote(task.task_number), task.task_folder]);

    csvData.unshift(headers);

    const csvContent = csvData.map((row) => row.map((cell) => (typeof cell === "string" && cell.includes(",") ? `"${cell}"` : cell)).join(",")).join("\n");

    const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);

    link.setAttribute("href", url);
    link.setAttribute("download", `tasks_export_${new Date().toISOString().split("T")[0]}.csv`);
    link.style.visibility = "hidden";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function getStatus(number) {
    return "Статус номера" + number;
  }

  // Вспомогательные функции для классов статусов
  function getGeoClass(status) {
    switch (status) {
      case "В работу":
        return "status-work";
      case "На решение":
        return "status-decision";
      case "Отказ":
        return "status-reject";
      default:
        return "status-bad";
    }
  }

  function getReferenceClass(status) {
    switch (status) {
      case "Подготовлена":
        return "status-ok";
      case "Нужна":
        return "status-warning";
      default:
        return "";
    }
  }

  function showError(message, suggestions) {
    errorDiv.style.display = "block";
    errorDiv.innerHTML = `<strong><i class="fas fa-exclamation-triangle"></i> ${message}</strong>`;

    if (suggestions && suggestions.length > 0) {
      let suggestionsHtml = '<div class="suggestion-title">Возможные пути:</div>';
      suggestions.forEach((suggestion) => {
        suggestionsHtml += `
                      <div class="suggestion-item" onclick="document.getElementById('folderPath').value='${suggestion}'; analyzeFolder('${suggestion}');">
                          <i class="fas fa-folder"></i> ${suggestion}
                      </div>
                  `;
      });
      suggestionsDiv.innerHTML = suggestionsHtml;
    }
  }

  // Сохранение заметки
  function saveNote(taskNumber, note) {
    taskNotes[taskNumber] = note;
    console.log("save", taskNotes);
    localStorage.setItem("taskNotes", JSON.stringify(taskNotes));
  }

  // Получение заметки
  function getNote(taskNumber) {
    return taskNotes[taskNumber] || "";
  }

  // Анализ при загрузке страницы
  analyzeFolder("");
});
