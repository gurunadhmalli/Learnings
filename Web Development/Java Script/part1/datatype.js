// this is the example for the single line comment
console.log("hello");

/*
premitive datatypes
Number
String
Boolean
Undefined
Null
Bigint
Symbol

non-premitive data types
object
    array
    set
    data
    map
    function
*/

// Number
let age = 22;
console.log(age, typeof age);
let price = 99.9;
console.log(price, typeof price);
let neg = 10;
console.log(neg, typeof age);

// String
let name = "guru";
let city = "kota";

console.log(`hell my name is ${name}`);
console.log(city, typeof city);

// Boolean
let isLoggedIn = true;
console.log(isLoggedIn, typeof isLoggedIn);

// undefined
let x;
console.log(x, typeof x);

//null
let a = null;
console.log(a, typeof a);
console.log(typeof null);

//BigInt

let BigNumber = 1234567812345790n;
console.log(BigNumber, typeof BigNumber);

//symbol

let id1 = Symbol("id");
let id2 = Symbol("id");
console.log(id1 == id2);

//variable declarations
//let
let FirstName = "Gurunadh";
FirstName = "malli";
console.log(FirstName);

//const
const LastName = "malli";
// LastName = "gurunadh";
console.log(LastName);

//var
var agee = 21;
var agee = 22;
console.log(agee);

let $name = "guru";
console.log($name);
