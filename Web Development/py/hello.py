# # x = 100
# # print(x)
# # print(id(x))

# # a = [1,2,3]
# # b = [1,2,3]

# # print(a == b)
# # print(a is b)



# import sys
# import gc

# a = [1,2,3]
# b  = a
# c = a
# c.append(4)

# print(gc.collect())
# print(sys.getrefcount(a))
# print(sys.getsizeof(a))

# # a = (1,2,3)
# # print(hash(a))


# # a = {(1,2,3):"guru"}
# # b = [1,2,3]
# # b.append(a)
# # print(b)


# a = [1,2,3]
# b = [1,2,3]
# a.append(b)
# print(a is b)


# a = 10
# b = 10
# b = 100
# print(a is b)


# a = b
# b = a
# print(a is b)