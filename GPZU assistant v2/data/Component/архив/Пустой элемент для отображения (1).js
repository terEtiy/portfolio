//console.log("element", el);
checkfulfilled = true;
// Глобальный счётчик для индексов
let globalIndex = 0;

selectedElementIndex = idx; // Укажите индекс элемента
inputNodes = 1; // Количество input узлов
outputNodes = 2; // Количество output узлов

console.log('response',response)

if(!response){
    createConnectionNodes(selectedElementIndex, inputNodes, outputNodes, load);
}

if(response){
    router(idx)
}

async function router(idx) {
    // Находим элемент по индексу
    const nodeToDelete = document.querySelector(`.node-el[data-number_index="${idx}"]`);
    
    // Добавляем класс для подсветки
    if (nodeToDelete) {
        nodeToDelete.classList.add('highlight');
        
        // Удаляем класс через 0.3 секунды
        setTimeout(() => {
            nodeToDelete.classList.remove('highlight');
        }, 300);
    }
    console.log("dataForConnect", dataForConnect)
    return;
  }