// create a function name teaordre and take the typetea parametre and retun them

function teaOrder(typeTea) {
  return `make ${typeTea}`;
}

console.log(teaOrder("lemon tea"));

// we need write the nested functions in the first function returns the second function and in the second
// in the second fucntion we need chai order is conformed and in the first function we nned have the teatype

function orderType(teaType) {
  function orderConformation() {
    return "chai is ordered";
  }
  return orderConformation();
}

let conformOrder = orderType("chai");
console.log(conformOrder);

//arrow function and create a calculate tool

// const calculateTool = (price, quantity) => price * quantity;

// console.log(calculateTool(10, 10));

//same in diffrenct way
const calculateTool = (price, quantity) => {
  return price * quantity;
};
console.log(calculateTool(10, 10));

//this is the hiher order function where one function take go into the input and return that function
function makeTea(typeTea) {
  return `make tea : ${typeTea}`;
}

function processTeaOrder(teaFunction) {
  return teaFunction("black coffe");
}

let order = processTeaOrder(makeTea);
console.log(order);

//

function createTeaMaker(name) {
  let score = 100;
  return function (teaType) {
    return `makeing ${teaType} ${score} ${name}`;
  };
}

let teaMaker = createTeaMaker("gurunadh");
console.log(teaMaker("chai"));

//fucntion with no input and output

function sayHello() {
  console.log("hi this is gurundh");
}

console.log(sayHello());

//function expression anther way of creating the function

const add = function (a, b) {
  return a * b;
};

console.log(add(10, 10));

function outer() {
  function inner() {
    return "hello";
  }
  return inner();
}

console.log(outer());
