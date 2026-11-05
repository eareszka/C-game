from pix import *

# Parts and where they attach, followed head to tail:
# head: top left, joins the neck at its back
# neck: arches up from the head, drops straight down left of the rider
# band 1: neck carries on down, IN FRONT of the hull, curves under the keel
# rise and hump: from under the keel, BEHIND the hull, comes up over the gunwale, arches right
# band 2: hump comes down IN FRONT of the hull near the stern, curves under the keel
# tail: from under the stern, climbs right of the boat, narrowing to a hook
# canoe: brown hull held inside the loops, bow left and stern right
# rider: hooded, sits in the canoe between band 1 and the rise, holds the paddle
# drip: red, falls from the mouth

V = '664b95'
D = '3b2a58'
G = 'a4aaba'
B = '815423'
R = 'b6433d'
K = (0, 0, 0, 255)

im = canvas(90, 70)
pen = ImageDraw.Draw(im)

# rise and hump, behind the canoe
pen.line([(46, 48), (46, 38), (47, 31), (51, 26), (56, 26), (60, 30), (61, 36)], fill=rgba(V), width=9, joint='curve')
pen.line([(49, 48), (49, 38), (50, 33), (53, 30), (55, 30), (57, 32), (58, 36)], fill=rgba(G), width=3, joint='curve')

# paddle, behind the rider
pen.line([(35, 16), (38, 35)], fill=rgba(B), width=2)
poly(im, [(33, 8), (36, 7), (38, 15), (35, 17)], B)

# rider
oval(im, 38, 25, 9, 16, G)
rect(im, 40, 29, 5, 4, D)
dot(im, 41, 30, R)
dot(im, 43, 30, R)
rect(im, 44, 34, 3, 4, D)

# canoe
poly(im, [(9, 30), (12, 30), (17, 37), (61, 37), (64, 30), (67, 30), (65, 40), (58, 47), (20, 47), (12, 40)], B)
rect(im, 40, 41, 12, 1, K)
rect(im, 44, 37, 7, 1, K)
rect(im, 15, 40, 6, 1, K)

# black edges where band 1 and band 2 lie over the hull
pen.line([(23, 38), (28, 47)], fill=K, width=1)
pen.line([(35, 37), (40, 47)], fill=K, width=1)
pen.line([(55, 37), (58, 47)], fill=K, width=1)
pen.line([(66, 37), (67, 41)], fill=K, width=1)

# head to band 1 and on under the keel
pen.line([(13, 9), (17, 7), (21, 7), (24, 9), (26, 13), (27, 18), (27, 30), (29, 38), (33, 45), (37, 51), (41, 54), (45, 53), (47, 48)], fill=rgba(V), width=9, joint='curve')
pen.line([(30, 16), (30, 30), (32, 37), (36, 43)], fill=rgba(D), width=2, joint='curve')
pen.line([(15, 12), (18, 11), (21, 11), (22, 13), (23, 18), (23, 30), (26, 39), (30, 46), (34, 53), (41, 57), (47, 56), (50, 50)], fill=rgba(G), width=3, joint='curve')

# belly plates, a few, unevenly spaced
rect(im, 22, 19, 3, 1, D)
rect(im, 22, 26, 2, 1, D)
rect(im, 24, 37, 3, 1, D)

# band 2 and tail
pen.line([(56, 26), (60, 30), (61, 38), (63, 46), (65, 51), (68, 53), (71, 50)], fill=rgba(V), width=9, joint='curve')
pen.line([(64, 34), (64, 39), (66, 45), (68, 48)], fill=rgba(D), width=2, joint='curve')
pen.line([(57, 32), (58, 39), (60, 47), (63, 54), (68, 57), (74, 52)], fill=rgba(G), width=3, joint='curve')
pen.line([(71, 50), (72, 44)], fill=rgba(V), width=8)
pen.line([(72, 44), (72, 36)], fill=rgba(V), width=6)
pen.line([(72, 36), (71, 28)], fill=rgba(V), width=5)
pen.line([(71, 28), (71, 21)], fill=rgba(V), width=4)
pen.line([(71, 21), (73, 15)], fill=rgba(V), width=3)
pen.line([(73, 15), (75, 13)], fill=rgba(V), width=2)
pen.line([(75, 13), (76, 17)], fill=rgba(V), width=1)
pen.line([(75, 50), (75, 44)], fill=rgba(G), width=2)
pen.line([(75, 44), (74, 36)], fill=rgba(G), width=2)
pen.line([(73, 36), (73, 28)], fill=rgba(G), width=1)

# head
poly(im, [(4, 5), (7, 3), (14, 2), (17, 3), (17, 9), (4, 9)], V)
poly(im, [(1, 9), (3, 5), (7, 3), (11, 3), (14, 6), (14, 9)], G)
poly(im, [(3, 10), (14, 10), (16, 12), (14, 14), (6, 13)], G)
rect(im, 2, 9, 12, 1, K)
rect(im, 7, 6, 2, 1, K)

# drip
rect(im, 4, 14, 2, 4, R)
rect(im, 4, 20, 1, 2, R)

im = outline(im)
save(im)
