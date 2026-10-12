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
console.log(dog.sound());

//exception

function Drink(type) {
  if (!new.target) {
    throw new Error("we need have the new if we want to call the drink");
  }
  this.type = type;
}

let campa = new Drink("campa");
let sprite = Drink("sprite");

//things we need learn
//this
//new
//construction
//prototype vs oop
// what type of programming that js is
