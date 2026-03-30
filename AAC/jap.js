let student = {
  fullname: "John Doe",
  rollno: 12345,
  age: 20,
};
console.log(student.fullname);
console.log(student.rollno);
console.log(student);
console.log(typeof student.age)
function greet(){
    console.log("Hello"+student.fullname)
}
function add(a, b){
    return a + b;
}
let result = add(5,6)
console.log(result);
function add(a, b){
    return a * b;
}
let r = add(5,6)
console.log(r)
const add  = (a, b) => 
    {
        return a * b;
    }
let res = add(5,6)
console.log(res)