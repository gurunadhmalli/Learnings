let username = {
  "first name": "guruandh",
  isLoggedin: true,
};
username.lastname = "malli";
username["first name"] = "sravani";

// console.log(username);
// console.log(username.lastname);
// console.log(username["first name"]);
// console.log(typeof username);

//date
let date = new Date();
console.log(date.getDate());

//array

let array = ["guruandh", "malli", true, 2];
console.log(array[0]);

//type converstion

let t = "1" + 1;
console.log(t, typeof t);

console.log(1 + true);
console.log(1 + false);
console.log(typeof Number(null));
console.log(Number(null));

console.log(Number(undefined));
console.log(typeof Number(undefined));

console.log(1 + "1" + true);
