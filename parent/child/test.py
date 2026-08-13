# def is_palindrome(s):
#     if s.lower() == s[::-1].lower():
#         return f'Yes, "{s}"" is palindrome'
#     else:
#         return f'No, "{s}" is palindrome'
# print(is_palindrome('Anna'))



# nums = [3, 8, 2, 10]
# print(max(nums))
#
# s = "Python"
# print(s[::-1])
# srev = ""
# for char in s:
#     srev = char[-1] + srev
# print(srev)
#
#
# a = 'level'
# print(a==a[::-1])
#
# b = 'banana'
# print("a:", b.count('a'), "b:", b.count('b'), "n:", b.count('n'))
#
# lst = [1, 2, 3, 4, 5, 3, 5, 1]
# st = set(lst)
# unique_list = []
# print(st)
# for item in lst:
#     if item not in unique_list:
#         unique_list.append(item)
# print(unique_list)
#
# lst1 = [1, 2, 3, 4, 5, 3, 5, 1]
# sort = set(lst1)
# lst2 = list(sort)
# print(lst2[-2])
#
# for i in range(1, 101):
#     if i % 3 ==0:
#         print(f"{i}: fizz")
#     elif i % 5 == 0:
#         print(f"{i}: buzz")
#     elif i % 15 == 0:
#         print(f"{i}: fizzbuzz")
#     else:
#         pass
#
# str1 = "Hello"
# glas = "aeiou"
# str2 = str1.lower()
# str3 = ""
# for char in str2:
#     if char in glas:
#         str3 += char
# print(str3)

# lst = [1, 2, 3, 4, 5, 3, 5, 1, 20, 34, 68, 64]
# print(sorted(lst)[-1])
#
#
# s = "Python"
# print(sorted(s, reverse=True))
# print(s[::-1])
# print(len(s))
# clean_lst = list(set(lst))
# print(sorted(clean_lst))
#
# target = 34
# for item in lst:
#     if item == target:
#         print(f'here is the target: {target}')


# lst1 = [1, 2, 3, 4]
# lst2 = [2, 3, 5, 6]
# print(set(lst1) | set(lst2))
#
# lst3 = [2, 1, 3, 2, 1, 5]
# for item in lst3:
#     if lst3.count(item) == 1:
#         print(item)
#         break
# lst4 = []
# for item in lst3:
#     if lst3.count(item) != 1:
#         lst4.append(item)
# print(set(lst4))


# def second_largest(lst):
#     sort_list = list(set(lst))
#     sorted_list = sorted(sort_list)
#     return sorted_list[-2]
# print(second_largest([1, 2, 3, 4, 5, 5]))
#
#
# def reverse_the_word(s):
#     split_s = s.split()
#     result = split_s[::-1]
#     return result
# print(reverse_the_word("Yulia is Voniuchka"))
#
# def remove_dupl(lst):
#     result = list(set(lst))
#     return result
# print(remove_dupl([1, 2, 3, 4, 5, 1, 2, 6]))
#
# def is_polindrome(str):
#     return str == str[::-1]
# print(is_polindrome("level"))
#
#
# print(5*(5+1) //2)

def count_vowels(s):
    vowels = "aeiou"
    str = ""
    for char in s:
        if char in vowels:
            str += char
    return len(str)
print(count_vowels("banana"))


def longest_word(s):
    words = s.split()
    long_word = ""
    for word in words:
        if len(word) > len(long_word):
            long_word = word
    return long_word
print(longest_word("Jacky is the most cute Pug in the world, and Yulia krasotka"))


def max_number(lst):
    sort_lst = sorted(lst)
    return sort_lst[-1]
print(max_number([1, 2, 3, 45, 4, 5, 25]))


def is_number_prime(number):
    if number == 2:
        return f"{number} is a prime"
    if number % number == 0 and number % 1 == 0 and number > 1 and number % 2 != 0:
        return f"{number} is a prime"
    else:
        return f"{number} isn't a prime"
print(is_number_prime(2))


def find_dupl(lst):
    dupl_list = []
    for i in lst:
        if lst.count(i) > 1 and i not in dupl_list:
            dupl_list.append(i)
    return dupl_list
print(find_dupl([1, 2, 3, 1, 4, 5, 5]))

def sum_digit(n):
    numbers = list(map(int, str(n)))
    return sum(numbers)
print(sum_digit(123))




