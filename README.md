# Seralix (Academic Prototype)

Seralix is an **academic programming language prototype** developed as a proof of capability in language design, parsing, and execution.

This version is **not intended to represent the final vision of Seralix**. Instead, it serves as a reduced prototype whose purpose is to demonstrate that a custom language can be designed and implemented from scratch, including:

- lexical analysis
- syntactic analysis
- abstract syntax tree construction
- basic execution semantics

In other words, this project is less about “the final Seralix” and more about:

> **showing that I am capable of building a programming language foundation myself**

---

# 1. Project Purpose

The goal of this prototype is to explore the essential components of a programming language implementation while keeping the system small enough to be completed and explained clearly.

This version focuses on:

- core syntax design
- parser construction
- interpreter behavior
- basic language semantics

It intentionally omits many advanced ideas planned for the broader Seralix vision, such as:

- type systems
- imports/modules
- package management
- advanced memory systems
- compile-time infrastructure
- optimization layers

This prototype should therefore be understood as a **minimal but functional language experiment**.

---

# 2. General Characteristics

Current Seralix prototype features include:

- expression parsing
- statement parsing
- functions
- conditions
- loops
- assignments
- literals
- basic built-in runtime values and functions

This version behaves more like a **small interpreted scripting language** than a complete systems language.

---

# 3. Program Structure

A Seralix program executes **top to bottom**, similarly to Python.

There is **no mandatory `main()` function**.

For example:

```slx
x = 10;
print(x);
````

is valid and executes directly.

Likewise:

```slx
function square(x) {
    return x * x;
}

print(square(5));
```

also works without requiring any special entry-point declaration.

---

# 4. Imports

This prototype currently has **no import system**.

All available names come from:

* values defined in the source file itself
* built-in runtime values/functions

That means there is currently no syntax such as:

```slx
import something
```

or module system support in this version.

---

# 5. Lexical Structure

## 5.1 Comments

Comments begin with `#` and continue until the end of the line.

```slx
x = 10;  # this is a comment
```

---

## 5.2 Identifiers

Identifiers are used for:

* variables
* function names
* parameter names

Examples:

```slx
x
my_value
powmod
primitive_root
```

---

## 5.3 Keywords

Current reserved keywords include:

```slx
and or
if elif else
while
for in
function return
```

These names cannot be used as normal identifiers.

---

# 6. Literals

Literals are direct values written in source code.

---

## 6.1 Number Literals

The language currently supports several Python-like numeric literal forms.

### Decimal integers

```slx
0
42
1_000_000
```

### Hexadecimal

```slx
0xFF
0xCAFE
```

### Octal

```slx
0o755
```

### Binary

```slx
0b101010
```

### Floating point

```slx
3.14
0.5
1e9
2.5e-3
```

### Imaginary / complex-style suffix

```slx
4j
2.5j
```

Examples:

```slx
x = 42;
y = 3.14;
mask = 0b1010;
```

---

## 6.2 String Literals

Strings can be written with single or double quotes.

### Single quoted

```slx
'hello'
```

### Double quoted

```slx
"hello"
```

### Triple single quoted

```slx
'''multi
line'''
```

### Triple double quoted

```slx
"""multi
line"""
```

Examples:

```slx
name = 'Seralix';
message = "Hello world";
```

---

## 6.3 Sequence Literals

Sequences are written with square brackets and behave as ordered collections.

```slx
[]
[1, 2, 3]
['a', 'b', 'c']
[1, 2 + 3, foo(4)]
```

Examples:

```slx
nums = [1, 2, 3, 4];
letters = ['a', 'b', 'c'];
```

---

# 7. Expressions

Expressions are constructs that produce values.

Examples:

```slx
1 + 2
x * y
foo(10)
a[i]
condition ? a : b
```

---

## 7.1 Grouping

Parentheses can be used to control evaluation order.

```slx
(1 + 2) * 3
(x + y) * z
```

---

## 7.2 Access, Indexing, Slicing, and Calls

---

### Member Access

```slx
obj.value
```

Used to access an attribute or member of an object.

---

### Indexing

```slx
a[0]
matrix[i]
```

Used to access elements of a sequence-like value.

---

### Slicing

```slx
a[1:5]
a[:10]
a[::2]
```

Used to extract subsequences.

---

### Function Calls

```slx
foo(x)
len(a)
pow(2, 10)
```

Used to call built-in or user-defined functions.

---

### Chained Examples

These postfix forms can be combined:

```slx
obj.method(x)[0]
```

---

# 8. Unary Operators

Unary operators act on a single operand.

Current unary operators:

```slx
+x
-x
~x
```

Examples:

```slx
-5
+value
~mask
```

---

# 9. Binary Operators

Binary operators act on two operands.

---

## 9.1 Arithmetic Operators

```slx
+
-
*
/
%
**
```

Examples:

```slx
x + y
a * b
base ** exp
```

---

## 9.2 Bitwise Operators

```slx
&
|
^
<<
>>
```

Examples:

```slx
x & 1
mask | flag
n >> 1
```

---

## 9.3 Comparison Operators

```slx
==
!=
<
<=
>
>=
```

Examples:

```slx
x == 0
a < b
count >= 10
```

---

## 9.4 Boolean Operators

```slx
and
or
```

Examples:

```slx
x > 0 and y > 0
a == b or c == d
```

---

# 10. Ternary Operator

The language supports a ternary conditional expression.

## Syntax

```slx
condition ? iftrue : iffalse
```

## Example

```slx
x % 2 == 0 ? 'even' : 'odd'
```

This returns:

* the middle expression if the condition is true
* the last expression otherwise

---

# 11. Operator Precedence

From **highest** to **lowest**, the current precedence is:

```text
postfix        () [] .
power          **
unary          + - ~
mul            * / %
add            + -
shift          << >>
bitwise        & ^ |
comparison     == != < <= > >=
boolean        and or
ternary        ? :
arrow          ->
```

This means, for example:

```slx
(x, y) -> x * y % 2 == 0 ? 'even' : 'odd'
```

is interpreted as:

```slx
(x, y) -> ((x * y % 2 == 0) ? 'even' : 'odd')
```

---

# 12. Functions

The prototype supports **two kinds of functions**:

* arrow functions
* named functions

---

# 12.1 Arrow Functions

Arrow functions are compact, expression-based functions.

## Syntax

```slx
(param1, param2=default, ...) -> expression
```

## Examples

```slx
() -> 42
(x) -> x * x
(x, y=10) -> x + y
(x, y) -> x * y % 2 == 0 ? 'even' : 'odd'
```

Arrow functions are useful for short functional expressions.

---

# 12.2 Named Functions

Named functions use the `function` keyword and a block body.

## Syntax

```slx
function name(param1, param2=default, ...) {
    ...
}
```

## Examples

```slx
function square(x) {
    return x * x;
}

function add(x, y=2) {
    return x + y;
}
```

---

## 12.3 Parameters and Defaults

Functions may define parameters with or without default values.

### Required parameters

```slx
function add(x, y) {
    return x + y;
}
```

### Default parameters

```slx
function add(x, y=2) {
    return x + y;
}
```

### Multiple defaults

```slx
function f(a, b=1, c=2) {
    return a + b + c;
}
```

### Rule

A non-default parameter **cannot** come after a default parameter.

This is invalid:

```slx
function f(x=1, y) {
    return x + y;
}
```

---

# 13. Statements

Statements are constructs that perform actions rather than simply producing values.

---

# 13.1 Assignment

Assignment is used to store values into variables or assignable targets.

## Basic assignment

```slx
x = 10;
a[i] = 5;
obj.value = 42;
```

## Augmented assignment

```slx
x += 1;
x -= 1;
x *= 2;
x /= 2;
x %= mod;
x **= 2;

x &= mask;
x |= flag;
x ^= bit;
x <<= 1;
x >>= 1;
```

Supported assignment operators:

```text
= += -= *= /= %= **=
&= |= ^= <<= >>=
```

---

# 13.2 Expression Statements

Any expression can be used as a statement if terminated with `;`.

Examples:

```slx
print(x);
foo(10);
bar(a, b);
```

This is useful for function calls with side effects.

---

# 13.3 If / Elif / Else

Conditional branching is supported using a Python-like style, but with **mandatory braces**.

## Syntax

```slx
if condition {
    ...
} elif other_condition {
    ...
} else {
    ...
}
```

## Example

```slx
if x < 0 {
    sign = -1;
} elif x == 0 {
    sign = 0;
} else {
    sign = 1;
}
```

### Notes

* parentheses around the condition are **not required**
* braces are **required**

---

# 13.4 While Loops

The `while` statement repeats a block while a condition remains true.

## Syntax

```slx
while condition {
    ...
}
```

## Example

```slx
i = 0;
while i < 10 {
    print(i);
    i += 1;
}
```

---

# 13.5 For-In Loops

The prototype supports Python-like iteration using `for ... in ...`.

## Syntax

```slx
for name in iterable {
    ...
}
```

## Example

```slx
for x in range(5) {
    print(x);
}
```

This loop assigns each element of the iterable to the loop variable.

---

# 13.6 Return

Functions can explicitly return values using `return`.

## Examples

```slx
return;
return x + 1;
return value;
```

Example inside a function:

```slx
function square(x) {
    return x * x;
}
```

---

# 14. Built-In Runtime Values

The prototype includes a small built-in runtime environment.

Current built-ins include:

```slx
print
pprint
range
bool
str
int
float
complex
len
true
false
null
```

Examples:

```slx
print('hello');
print(len([1, 2, 3]));
for x in range(5) {
    print(x);
}
```

---

# 15. Example Programs

---

## 15.1 Basic Arithmetic

```slx
x = 10;
y = 20;
print(x + y);
```

---

## 15.2 Function Example

```slx
function add(x, y=2) {
    return x + y;
}

print(add(5));
print(add(5, 10));
```

---

## 15.3 Conditional Example

```slx
x = 7;

if x % 2 == 0 {
    print('even');
} else {
    print('odd');
}
```

---

## 15.4 Loop Example

```slx
i = 0;

while i < 5 {
    print(i);
    i += 1;
}
```

---

## 15.5 For-In Example

```slx
for x in range(5) {
    print(x);
}
```

---

## 15.6 Arrow Function Example

```slx
is_even = (x) -> x % 2 == 0 ? true : false;
print(is_even(4));
```

---

# 16. Current Limitations

This prototype is intentionally limited.

Known limitations include:

* no import/module system
* no static type system
* no classes/objects as a formal user-defined feature
* no package manager
* no full standard library
* no compile-time facilities
* sequence append is not yet a dedicated built-in language operation
* `/` currently follows interpreter-defined behavior and may require refinement for integer-heavy algorithms

These limitations are expected and acceptable for the purpose of this academic prototype.

---

# 17. Final Note

This project should not be interpreted as the full Seralix vision.

Instead, it should be understood as a **proof of capability**:

* proof that a custom language can be designed
* proof that parsing and runtime semantics can be implemented
* proof that the author is capable of constructing the foundations of a language system independently

That is the real purpose of this prototype.

---

# 18. Author Statement

This prototype represents an important milestone:

> not “the final Seralix,”
> but the confirmation that building Seralix is genuinely within reach
