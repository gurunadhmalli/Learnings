function Person(name) {
  this.name = name;
}

Person.prototype.greet = function () {
  return `hello this is the ${this.name}`;
};

let gurunadh = new Person("gurunadh");
console.log(gurunadh.greet());
