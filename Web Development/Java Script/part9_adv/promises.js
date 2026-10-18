function fectchData() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      let success = true;
      if (success) {
        resolve("Data fetched success fully");
      } else {
        reject("error fetching in the data");
      }
    }, 4000);
  });
}

fectchData()
  .then((data) => {
    console.log(data);
    return "gurunadh";
  })
  .then((value) => console.log(value))
  .catch((error) => console.log(error));

//topics we need to learn here
//promise and promise chaining
