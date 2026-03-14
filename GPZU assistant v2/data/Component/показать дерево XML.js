//console.log("element", el);
checkfulfilled = true;
// Глобальный счётчик для индексов
let globalIndex = 0;

let inputData = null;
let outputData = null;

selectedElementIndex = idx; // Укажите индекс элемента
inputNodes = 1; // Количество input узлов
outputNodes = 1; // Количество output узлов

if (!response) {
  createConnectionNodes(selectedElementIndex, inputNodes, outputNodes, load);
}

if (response) {
  router(idx);
}

async function router(idx) {
  // Находим элемент по индексу
  const node = document.querySelector(`.node-el[data-number_index="${idx}"]`);

  // Добавляем класс для подсветки
  if (node) {
    node.classList.add("highlight");

    // Удаляем класс через 0.3 секунды
    setTimeout(() => {
      node.classList.remove("highlight");
    }, 300);
  }

  if (Array.isArray(dataForConnect)) {
    /// Дебаг

    console.groupCollapsed(`%c Данные перед помещением в целевой узел`, "color: blue; font-weight: bold;");
    console.log(dataForConnect);
    console.groupEnd();

    /// нужно перемещать данные из element.type = 1 в element.type = 0 ...........................................

    dataForConnect.forEach((element) => {
      if (element.Connection == null) {
        console.log("type = 1", element);
        placeDataPoint = element.data;
        showTree(placeDataPoint, idx);
        placeIndexPoint = element.index;
        placeTypePoint = element.TypePont;
      }
    });

    dataForConnect.forEach((element) => {
      if (element.Connection !== null) {
        console.log("type = 0", element);
        placeData(idx, element.index, element.TypePont, placeDataPoint, true, placeIndexPoint, placeTypePoint);
      }
    });
  }

  if (Array.isArray(dataForConnect)) {
    console.log("Перемещение данных из целевого узла (скрипт инициатор): ");

    dataForConnect.forEach((element) => {
      console.log("element", element);
      if (element.Connection) {
        console.table({
          "Индекс ноды (Откуда)": idx,
          "Индекс целевого узла (Откуда)": element.index,
          "Тип целевого узла (Откуда)": element.TypePont,
          "Индекс ноды (Куда)": element.Connection.endElement_idx,
          "Индекс целевого узла (Куда)": element.Connection.point_idx,
          "Тип целевого узла (Куда)": element.Connection.type_idx,
        });
        console.groupEnd();

        MoveData(Number(idx), Number(element.index), Number(element.TypePont), Number(element.Connection.endElement_idx), Number(element.Connection.point_idx), Number(element.Connection.type_idx));
      } else {
        console.log("Перемещение даных остновлено скриптом");
      }
    });
  }

  return;
}

async function showTree(placeDataPoint, idx) {
  const node = document.querySelector(`.node-el[data-number_index="${idx}"]`);
  const prevNode = node.querySelector(".preview-result");
  prevNode.innerHTML = ""; // Очищаем перед добавлением нового дерева

  console.log("placeDataPoint", placeDataPoint);

  if (!placeDataPoint || !placeDataPoint[0]?.content) {
    console.error("Некорректные данные для XML");
    return;
  }

  const xmlString = new XMLSerializer().serializeToString(placeDataPoint[0].content);
  const parser = new DOMParser();
  const xmlDoc = parser.parseFromString(xmlString, "application/xml");

  // Создаём контейнер для дерева
  const container = document.createElement("div");
  container.classList.add("xml-tree-container");
  container.style.cssText = `
  max-height: 380px;
  overflow-y: auto;
  border: 1px solid #aaa;
  padding: 8px;
  background: #f9f9f9;
  border-radius: 5px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  font-family: cursive;
  white-space: white-space;
  word-break: break-word;
  scrollbar-width: thin;
  scrollbar-color: #999 #f9f9f9;
  text-align: start;
`;

  // Стилизация скроллбара для Webkit (Chrome, Edge, Safari)
  container.innerHTML += `
  <style>
    .xml-tree-container::-webkit-scrollbar {
      width: 8px;
    }
    .xml-tree-container::-webkit-scrollbar-thumb {
      background: #999;
      border-radius: 4px;
    }
    .xml-tree-container::-webkit-scrollbar-thumb:hover {
      background: #777;
    }
  </style>
`;

  // Строка поиска
  const searchInput = document.createElement("input");
  searchInput.type = "text";
  searchInput.placeholder = "Поиск по тегам и данным...";
  searchInput.style.cssText = `
  width: 90%;
  padding: 8px 12px;
  margin-bottom: 8px;
  border: 1px solid #aaa;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
  transition: border-color 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
  outline: none;
`;

  // Добавляем эффект фокуса
  searchInput.addEventListener("focus", () => {
    searchInput.style.borderColor = "#007bff";
    searchInput.style.boxShadow = "0 0 5px rgba(0, 123, 255, 0.5)";
  });

  searchInput.addEventListener("blur", () => {
    searchInput.style.borderColor = "#aaa";
    searchInput.style.boxShadow = "none";
  });

  // Контейнер для вывода количества найденных элементов
  const resultCount = document.createElement("div");
  resultCount.style.cssText = `
  font-size: 14px;
  color: #555;
  margin-bottom: 5px;
`;
  container.prepend(resultCount);

  let searchResults = []; // Массив найденных элементов
  let searchIndex = -1; // Текущий индекс найденного элемента

  // Функция для раскрытия родительских тегов
  function expandParents(element) {
    while (element && element !== container) {
      if (element.tagName === "UL") {
        element.style.display = "block";
      }
      element = element.parentElement;
    }
  }

  // Обработчик поиска
  searchInput.addEventListener("input", function () {
    const searchValue = searchInput.value.toLowerCase();
    searchResults = [];
    searchIndex = -1;

    const tags = container.querySelectorAll(".xml-tag, .xml-value");
    tags.forEach((tag) => {
      if (tag.textContent.toLowerCase().includes(searchValue) && searchValue.length > 0) {
        tag.style.background = "yellow";
        searchResults.push(tag);
        expandParents(tag); // Раскрываем родительские теги
      } else {
        tag.style.background = "transparent";
      }
    });

    resultCount.textContent = searchResults.length > 0 ? `Найдено: ${searchResults.length}` : "Ничего не найдено";
  });

  // Обработчик навигации по найденным элементам (по Enter)
  searchInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && searchResults.length > 0) {
      event.preventDefault();

      // Убираем выделение с предыдущего найденного элемента
      if (searchIndex >= 0) {
        searchResults[searchIndex].style.background = "yellow";
      }

      // Переход к следующему найденному элементу
      searchIndex = (searchIndex + 1) % searchResults.length;
      searchResults[searchIndex].style.background = "orange";

      // Прокрутка к текущему найденному элементу
      searchResults[searchIndex].scrollIntoView({ behavior: "smooth", block: "center" });
    }
  });

  // Контейнер для отображения пути к элементу
  const pathContainer = document.createElement("div");
  pathContainer.style.cssText = `
  font-size: 14px;
  color: #444;
  margin-bottom: 10px;
  padding: 5px;
  border-bottom: 1px solid #ccc;
  white-space: nowrap;
  overflow-x: auto;
  display: flex;
  align-items: center;
  gap: 10px;
`;
  container.prepend(pathContainer);

  // Кнопка для копирования пути
  const copyButton = document.createElement("button");
  copyButton.textContent = "Копировать путь";
  copyButton.style.cssText = `
  background: #007bff;
  color: white;
  border: none;
  padding: 5px 10px;
  cursor: pointer;
  border-radius: 3px;
  display: none;
`;

  copyButton.addEventListener("click", () => {
    if (copyButton.dataset.path) {
      navigator.clipboard.writeText(copyButton.dataset.path).then(() => {
        copyButton.textContent = "Скопировано!";
        setTimeout(() => (copyButton.textContent = "Копировать путь"), 1500);
      });
    }
  });

  pathContainer.appendChild(copyButton);

  function getElementPathInXML(element, container) {
    let pathSet = new Set(); // Используем Set для хранения уникальных значений
    while (element && element !== container) {
      if (element.nodeType === Node.ELEMENT_NODE) {
        // Получаем имя тега, но только если это элемент
        let tag = element.querySelector(".xml-tag");
        //console.log("tag", tag);

        // Если тег содержит данные, добавляем его в Set
        if (tag) {
          pathSet.add(tag.textContent); // Добавляем значение в Set
        }
      }
      element = element.parentElement; // Переходим к родительскому элементу
    }
    return Array.from(pathSet).join(" > "); // Преобразуем Set в массив и возвращаем путь, разделенный " > "
  }

  // Функция для создания дерева XML
  function createTree(node) {
    const ul = document.createElement("ul");
    ul.style.listStyle = "none";
    ul.style.paddingLeft = "15px";

    Array.from(node.childNodes).forEach((child) => {
      const li = document.createElement("li");

      if (child.nodeType === Node.ELEMENT_NODE) {
        const tag = document.createElement("span");
        tag.textContent = `<${child.nodeName}>`;
        tag.classList.add("xml-tag");
        tag.style.cssText = "color: blue; cursor: pointer; display: block;";

        const childContainer = createTree(child);
        childContainer.style.display = "none"; // Скрываем вложенные теги

        tag.addEventListener("click", () => {
          childContainer.style.display = childContainer.style.display === "none" ? "block" : "none";
        });

        li.appendChild(tag);
        li.appendChild(childContainer);
      } else if (child.nodeType === Node.TEXT_NODE && child.nodeValue.trim()) {
        const textNode = document.createElement("span");
        textNode.textContent = child.nodeValue;
        textNode.classList.add("xml-value");
        textNode.style.cssText = "color: green; cursor: pointer;";

        textNode.addEventListener("click", (event) => {
          // Получаем путь к элементу
          const path = getElementPathInXML(event.target, container);

          // Обновляем кнопку копирования
          copyButton.style.display = "inline-block";
          copyButton.dataset.path = path;

          // Создаём ссылку на элемент
          pathContainer.innerHTML = "";
          pathContainer.appendChild(copyButton);

          const pathLink = document.createElement("span");
          pathLink.textContent = path;
          pathLink.style.cssText = "color: #007bff; cursor: pointer; text-decoration: underline;";

          pathLink.addEventListener("click", () => {
            textNode.style.background = "orange";
            setTimeout(() => (textNode.style.background = "transparent"), 1500);
            textNode.scrollIntoView({ behavior: "smooth", block: "center" });
          });

          pathContainer.appendChild(pathLink);
        });

        li.appendChild(textNode);
      }
      ul.appendChild(li);
    });

    return ul;
  }

  const tree = createTree(xmlDoc.documentElement);
  container.appendChild(searchInput);
  container.appendChild(tree);
  prevNode.appendChild(container);
}
