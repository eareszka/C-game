# Style families: my read after looking at every sprite. Metrics below only test whether the read holds up.
FAM = {
 'A': [0,1,2,3,4,5,8,9,11,14,15,24,43,50,53,54,55,65,66,68],
 'B': [7,16,18,21,22,25,26,28,29,32,33,36,39,40,44,47,56,57,58,59,60,62,69,70,71,72,73,74,76,77,78,82,86,88,89,91,93,94],
 'C': [10,17,19,20,27,35,37,38,41,42,45,61,64,67,75,79,81,83,85,87,90,92,96],
 'D': [12,13,31,34,46,51,63,80,84,95,97,99,100],
 'E': [6,23,30,48,49,52,98],
}
FAM_OF = {i: k for k, v in FAM.items() for i in v}
assert sorted(FAM_OF) == list(range(101)), set(range(101)) - set(FAM_OF)
