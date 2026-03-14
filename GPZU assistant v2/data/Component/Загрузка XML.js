//console.log("element", el);
checkfulfilled = true;
// Глобальный счётчик для индексов
let globalIndex = 0;

selectedElementIndex = idx; // Укажите индекс элемента
inputNodes = 1; // Количество input узлов
outputNodes = 0; // Количество output узлов

if (!response) {
  createConnectionNodes(selectedElementIndex, inputNodes, outputNodes, load);
}

if (response) {
  router(idx);
}

async function router(idx) {
  // Находим элемент по индексу
  const nodeToDelete = document.querySelector(`.node-el[data-number_index="${idx}"]`);

  // Добавляем класс для подсветки
  if (nodeToDelete) {
    nodeToDelete.classList.add("highlight");

    // Удаляем класс через 0.3 секунды
    setTimeout(() => {
      nodeToDelete.classList.remove("highlight");
    }, 300);
  }

  if (Array.isArray(dataForConnect)) {
    /// Дебаг

    console.groupCollapsed("Данные перед отправкой");
    console.table(
      dataForConnect.map((element) => ({
        idx,
        "element.index": element.index,
        "element.TypePont": element.TypePont,
        "XML Contents": xmlContents,
      }))
    );
    console.groupEnd();

    dataForConnect.forEach((element) => {
      placeData(idx, element.index, element.TypePont, xmlContents);
    });
  }

  if (Array.isArray(dataForConnect)) {
    console.log("Перемещение данных из целевого узла (скрипт инициатор): ");

    dataForConnect.forEach((element) => {
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

function downloadXML(selectedElementIndex) {
  // Ищем элемент с атрибутом data-number_index, равным selectedElementIndex
  const previewResultEL = Array.from(document.querySelectorAll(".node-el")).find((element) => {
    return element.getAttribute("data-number_index") == selectedElementIndex;
  });

  // Если элемент найден, ищем его дочерний элемент с классом .preview-result
  if (previewResultEL) {
    let resultElement = previewResultEL.querySelector(".preview-result");
    let headNode = previewResultEL.querySelector(".head-node");

    // Инициализация хранилища для XML данных
    let count = 0;

    headNode.textContent = "Загрузка XML";

    resultElement.textContent = `Перетащите файлы сюда \n Файлов загружено: ${count}`;
    resultElement.style.textAlign = "-webkit-center";
    resultElement.style.whiteSpace = "break-spaces";
    resultElement.style.border = "2px dashed #007BFF";

    // Общая функция обработки файлов
    const handleFiles = (files) => {
      Array.from(files).forEach((file) => {
        xmlContents = [];
        const reader = new FileReader();

        reader.onload = function (e) {
          const parser = new DOMParser();
          const xmlDoc = parser.parseFromString(e.target.result, "text/xml");

          // Добавляем результат в массив
          xmlContents.push({
            filename: file.name,
            content: xmlDoc,
          });

          // Обновляем счетчик
          count++;
          resultElement.textContent = `Перетащите файлы сюда \n Файлов загружено: ${count}`;

          // Выводим в консоль
          console.log("Загруженные XML данные:", xmlContents);
        };

        reader.readAsText(file);
      });
    };

    // Обработчики событий
    resultElement.addEventListener("dragover", (event) => {
      event.preventDefault();
      resultElement.classList.add("dragover");
    });

    resultElement.addEventListener("dragleave", () => {
      resultElement.classList.remove("dragover");
    });

    resultElement.addEventListener("drop", (event) => {
      event.preventDefault();
      resultElement.classList.remove("dragover");
      handleFiles(event.dataTransfer.files);
    });

    // Унифицированный обработчик для input
    document.getElementById("fileInput").addEventListener("change", function (event) {
      handleFiles(event.target.files);
      event.target.value = ""; // Очищаем input для возможности повторной загрузки
    });

    return resultElement; // Возвращаем найденный элемент
  } else {
    console.log("Element not found");
    return null; // Если элемент не найден, возвращаем null
  }
}

if (!response) {
  downloadXML(idx);
}
