function* printNumbers() {
  yield 1;
  yield 2;
  yield 3;
}

const gen = printNumbers();
const genTwo = printNumbers();

console.log(gen.next().value);
console.log(gen.next().value);
console.log(gen.next().value);

console.log(genTwo.next().value);
console.log(genTwo.next().value);
