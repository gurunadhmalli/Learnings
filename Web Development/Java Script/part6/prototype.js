let computer = { cpu: 12 };
let lenovo = {
  screen: "HD",
  __proto__: computer,
};
let tomHardware = {};

// console.log(`lenovo `, lenovo.__proto__);

let genericCar = { tyres: 4 };

let tesla = {
  driver: "AI",
};

Object.setPrototypeOf(tesla, genericCar);

// console.log(`tesla `, Object.getPrototypeOf(tesla));

/*Imagine you are building an application for TradeEximOS,
 and you need to create multiple users.Each user has a name
  and a method to log in.*/

const user1 = {
  name: "Ravi",
  login: function () {
    console.log(`${this.name} logged in`);
  },
};

const user2 = {
  name: "Krishna",
  login: function () {
    console.log(`${this.name} logged in`);
  },
};

// user1.login(); // Ravi logged in
// user2.login(); // Krishna logged in

// We have written the same login()
// method twice. If we have 1,000 users,
// duplicating methods in every object is inefficient.

//first proto type

const userProtoType = {
  login() {
    console.log(`${this.name} used is loged in`);
  },
};

const user3 = Object.create(userProtoType);
user3.name = "gurunadh";
// user3.login();

//how can two objects share the same login method

const user4 = Object.create(userProtoType);
console.log(user4.__proto__); // this both for the insepation
console.log(Object.getPrototypeOf(user4));
user4.name = "srinu";
user4.login();
// console.log(user3.name == user4.name);
// console.log(user3.login == user4.login);

//
const parent = {
  greet() {
    console.log("Hello!");
  },
};

const child = {
  name: "Ravi",
};

Object.setPrototypeOf(child, parent);

child.greet();

console.log(Object.getPrototypeOf(child) === parent);
