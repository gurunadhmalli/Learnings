function Person(name, age) {
  this.name = name; // here this refrer to the contest of the function like this particular parametre from this function
  this.age = age;
}

function Car(make, model) {
  this.make = make;
  this.model = model;
}

let myCar = new Car("suzuki", "swift"); // new is for creating the new instsnce or object and without this we get the undefined
// console.log(myCar);

let myFriendCar = new Car("tata", "range rover");
// console.log(myFriendCar);

//we can able to describe the a function in this

function typeTea(type) {
  this.type = type;
  this.describe = function () {
    return `this is the type of tea ${type}`;
  };
}

let tea = new typeTea("chia");
// console.log(tea.describe());

//
function Animal(species) {
  this.species = species;
}

Animal.prototype.sound = function () {
  return `${this.species} make the sound`;
};

let dog = new Animal("dog");
// console.log(dog.sound());

//exception

// function Drink(type) {
//   if (!new.target) {
//     throw new Error("we need have the new if we want to call the drink");
//   }
//   this.type = type;
// }

// let campa = new Drink("campa");
// let sprite = Drink("sprite");

//how to create the constructor function

function Employee(name, age, salary) {
  this.name = name;
  this.age = age;
  this.salary = salary;
}

const emp1 = new Employee("gurunadh", 25, 3000);
const emp2 = new Employee("srinu", 25, 25000);
console.log(emp1.name);
console.log(emp2.salary);
