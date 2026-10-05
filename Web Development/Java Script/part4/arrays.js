/* we need to access the create a array have 
the tea name and array name teaFlovers and access 
the first element store in the varaible name firstTea
*/

let teaFlovers = ["orange tea", "lemon tea", "honey tea"];
const firstTea = teaFlovers[0];
console.log(firstTea);

//accsing the favorite city of the array

let cities = ["kota", "nellore", "hyderabad", "banglore"];

const favoriteCity = cities[2];
console.log(favoriteCity);

// we need use the method to push a elemet and lenght

let fruites = ["bannana", "apple"];
fruites.push("avacado");
console.log(fruites); //using the push. to push the element to the last index
fruites[fruites.length] = "mango"; //using the length of the element
console.log(fruites);

//use the pop method to remove the last elemt

let veg = ["carrot", "bitroot", "oninon", "brinjal"];

const secVeg = veg.pop();
console.log(veg);
//we can also ablet to retrun the pop value
console.log(secVeg);

//softcopy the array and manupulate the one of the element in the array

let electroAppliences = ["tv", "fan", "wifi", "ac"];
let softElectroAppliences = electroAppliences;
electroAppliences.pop();
console.log(electroAppliences);
console.log(softElectroAppliences);

// hard copy of the array

let a = [1, 2, 3, 4];
//this will do the hard copy
let hardA = [...a];
// let hardA = a.slice();
a.pop();
console.log(a);
console.log(hardA);

//merge two array using the concate method of the array

let firstNumbers = [1, 2, 3, 4, 5];
let lasstNumbers = [6, 7, 8, 9];
let cominedNumbers = firstNumbers.concat(lasstNumbers);
// let cominedNumbers = [firstNumbers,lasstNumbers] -> this will give the 2d array
// let cominedNumbers = firstNumbers+lasstNumbers ->this will give the string as the output
console.log(cominedNumbers);

//find the length of the array

let menu = ["samosa", "tea", "coffe"];

const len = menu.length;
console.log(len);

// checke the particulat elment present in the array

let num = [1, 2, 3, 4, 5];
let isNumPresent = num.includes(4);
console.log(isNumPresent);
