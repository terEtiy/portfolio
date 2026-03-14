//console.log("element", el);
checkfulfilled = true;
// Глобальный счётчик для индексов
let globalIndex = 0;

selectedElementIndex = idx; // Укажите индекс элемента
inputNodes = 4; // Количество input узлов
outputNodes = 12; // Количество output узлов

createConnectionNodes(selectedElementIndex, inputNodes, outputNodes, load);
