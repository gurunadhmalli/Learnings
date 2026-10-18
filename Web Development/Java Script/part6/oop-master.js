let car = {
  make: "suzuki",
  model: "swift",
  year: 2020,
  start: function () {
    return `${this.model} in the year ${this.year}`;
  },
};

//console.log(car.start()); here we are not able to create much of copies of it above way that is the where we oops

//constructor function
function Person(name, age) {
  this.name = name;
  this.age = age;
}

let guru = new Person("guru", 21);
// console.log(guru);

//using the prototype
function Animal(type) {
  this.type = type;
}

Animal.prototype.speak = function () {
  return `${this.type} is make sound`;
};

Array.prototype.guru = function () {
  return `${this} is an custom array method`;
};

let array = [1, 2, 3];
// console.log(array.guru());
let myArray = [1, 2, 3, 1, 2, 3];
// console.log(myArray.guru());

class Vehicle {
  constructor(make, model) {
    this.make = make;
    this.model = model;
  }

  start() {
    return `${this.model} made by the ${this.make}`;
  }
}

class Car extends Vehicle {
  drive() {
    return `${this.make} this is the inheritance example`;
  }
}

let myCar = new Car("suzuki", "swift");
// console.log(myCar.start());
// console.log(myCar.drive());

//encapsulation

class bankAccount {
  #balance = 0;

  deposit(amount) {
    this.#balance += amount;
    return this.#balance;
  }

  getBalance() {
    return `$ ${this.#balance}`;
  }
}

let account = new bankAccount();
console.log(account.getBalance());

//abstraction

class CoffeMachine {
  start() {
    return `starting the coffe machine`;
  }

  prepare() {
    return `preparing the coffe`;
  }

  pressStartButton() {
    let s = this.start();
    let p = this.prepare();
    return `${s + p}`;
  }
}

let myMchine = new CoffeMachine();
// console.log(myMchine.start());
// console.log(myMchine.prepare());
console.log(myMchine.pressStartButton());

//polymorphism

class Bird {
  fly() {
    return `Flying ...`;
  }
}

class Penguin extends Bird {
  fly() {
    return `i am not able to fly`;
  }
}

let bird = new Bird();
// console.log(bird.fly());
let penguin = new Penguin();
// console.log(penguin.fly());

//static method
class Caluculator {
  static add(a, b) {
    return a + b;
  }
}

// console.log(Caluculator.add(1, 2));

// Getters and setters

class Employee {
  #salary;
  constructor(name, salary) {
    if (salary < 0) {
      throw new Error("Salary cannot be in negative");
    }
    this.name = name;
    this.#salary = salary;
  }

  get salary() {
    return `You are not allowed to see salary`;
  }

  set salary(value) {
    if (value < 0) {
      console.error("Invalid Salary");
    } else {
      this._salary = value;
    }
  }
}
let emp = new Employee("Alice", -50000);
console.log(emp._salary);
emp.salary = 60000;
