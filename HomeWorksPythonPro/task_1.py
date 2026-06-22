# Strings
def length_string(my_str):
    return len(my_str)
print(length_string("hello"))

def join_str(first_string: str, second_string: str):
    return " ".join([first_string, second_string])
print(join_str("hello", "world"))


#Int, Float
def square(num):
    return num * num
print(square(5))

def summary(first, second):
    return first + second
print(summary(1, 2))

def divide(num1: int, num2: int):
    return divmod(num1, num2)
print(divide(1, 2))


#Lists
def average(list):
    return sum(list) / len(list)
print(average([1, 2, 3, 4, 5]))

def merge_lists(list1, list2):
    result = list(set(list1) & set(list2))
    return result
print(merge_lists([1, 2, 3, 4, 5], [3, 4, 5, 6, 7]))


# Dictionaries
def key_return(dict):
    return list(dict.keys())
print(key_return({"a": 1, "b": 2}))

def add_dict(dict1, dict2):
    return dict1 | dict2
print(add_dict({"a": 1, "b": 2}, {"c": 3}))


#Sets
def merge_sets(set1, set2):
    return set1 | set2
print(merge_sets({1, 5, True}, {"Hello", 3,"World", 4}))

def is_subset(set1, set2):
    return set1.issubset(set2)
print(is_subset({1, 5, True}, {"Hello", 3,"World", 4}))


#Loops
def is_number_even(num):
    if num % 2 == 0:
        return "Even"
    else:
        return"Odd"
print(is_number_even(4))

def even_numbers(my_list):
    result = []
    for num in my_list:
        if num % 2 == 0:
            result.append(num)
    return result
print(even_numbers([1, 2, 3, 4, 5]))


#Lambda
even_num = lambda num: "Even" if num % 2 == 0 else "Odd"
print(even_num(5))

