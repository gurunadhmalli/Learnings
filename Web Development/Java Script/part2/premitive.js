// number

let balance = 120;
console.log(balance);
console.log(typeof balance);

let anotherBalance = new Number(120);
console.log(anotherBalance.valueOf());
console.log(typeof anotherBalance);

//bolean
let isActive = true;
console.log(isActive, typeof isActive);
let isRealActive = new Boolean(true);
console.log(isRealActive.valueOf(), typeof isRealActive);

//unideifened and null
let firstname = null;
let lastname = undefined;
console.log(firstname, typeof firstname);
console.log(lastname, typeof lastname);

//string
let username = "guru";

let oldGreetMsg = "hello" + " " + username;
console.log(oldGreetMsg);

let newGreetMsg = `hello ${username}`;
console.log(newGreetMsg);

console.log(`the value of ${2 * 2}`); //we can able to do the computation

//symbol
let s = Symbol();
let s2 = Symbol();
console.log(s == s2);
