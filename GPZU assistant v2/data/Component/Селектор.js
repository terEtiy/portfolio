//console.log("element", el);
checkfulfilled = true;
// Глобальный счётчик для индексов
let globalIndex = 0;

let inputData = null;
let outputData = null;

selectedElementIndex = idx; // Укажите индекс элемента
inputNodes = 2; // Количество input узлов
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

async function selector(placeDataPoint, idx) {}
