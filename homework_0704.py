import numpy as np

a = 4
b = 4

# t1
t1 = np.ones((a, a), dtype=int)
t1[1:-1, 1:-1] = 0

# t2
t2 = np.diag(np.arange(1, b+1))

# t3，t4
t3 = np.random.randint(0, 10, size=(4, 4))
argmax_0 = np.argmax(t3, axis=0)
argmin_0 = np.argmin(t3, axis=0)
argmax_1 = np.argmax(t3, axis=1)
argmin_1 = np.argmin(t3, axis=1)
t4 = np.vstack([argmax_0, argmin_0, argmax_1, argmin_1])

# t5
t5 = t1 + t2 - t3 + t4
t5 = np.where(t5 < 0, 0, 1)
t5 = t5.flatten()

# Print the results
print("t1:\n", t1)
print("t2:\n", t2)
print("t3:\n", t3)
print("t4:\n", t4)
print("t5:\n", t5)