from pix import *

im = canvas(79, 79)
K = '000000'
S = '34343e'
R = '474751'
L = '595965'
G = '4fa667'
D = '29633e'
H = 'a8f0bc'

# The cowl opens around the bare head; the robe hangs in angular folds.
poly(im, [(26,10),(31,7),(48,7),(54,12),(59,14),(64,22),
          (62,32),(60,40),(63,51),(66,62),(69,73),(67,77),
          (57,78),(47,76),(41,78),(31,77),(25,78),(15,75),
          (13,70),(18,59),(21,47),(21,35),(18,27),(20,18)], R)
poly(im, [(27,11),(32,9),(49,9),(53,13),(47,16),(32,18),(24,23),(21,20)], L)
poly(im, [(26,13),(31,13),(31,20),(26,24),(21,22)], S)
poly(im, [(51,12),(56,16),(52,21),(45,25),(32,27),(24,24),
          (25,21),(35,23),(45,21)], K)
poly(im, [(53,16),(57,16),(54,20),(46,24),(46,21)], L)
poly(im, [(25,28),(32,29),(32,41),(28,47),(25,58),(23,68),
          (27,72),(21,72),(18,69),(22,55)], L)
poly(im, [(53,29),(59,27),(57,42),(60,54),(64,66),(65,73),
          (56,74),(52,67),(53,54),(49,45)], S)
poly(im, [(40,44),(45,44),(43,52),(42,62),(46,72),(49,75),
          (43,75),(38,67),(37,59)], S)
poly(im, [(31,52),(34,48),(33,61),(30,69),(34,74),(29,72),(27,67)], S)
# Seams, overlapping cloth and a ragged hem, all in deliberate short runs.
poly(im, [(25,30),(27,31),(26,39),(23,43),(23,38)], K)
poly(im, [(54,29),(56,30),(54,38),(52,40),(52,35)], K)
poly(im, [(35,50),(37,52),(35,61),(36,66),(34,64),(33,60)], K)
poly(im, [(46,53),(48,56),(47,64),(50,70),(48,70),(45,65)], K)
poly(im, [(20,66),(21,70),(26,73),(31,73),(33,76),(25,75),(20,72)], K)
poly(im, [(54,67),(57,71),(61,72),(64,72),(65,74),(58,74),(54,71)], K)
rect(im, 39,73,3,3,K)
rect(im, 16,75,5,2,S)
rect(im, 57,76,5,2,S)
rect(im, 30,75,4,2,L)

# Left sleeve and the green hand held out toward the player.
poly(im, [(21,22),(25,26),(23,35),(18,39),(13,35),(12,28),(15,24)], S)
poly(im, [(18,24),(22,25),(21,31),(17,34),(14,31)], R)
poly(im, [(17,32),(15,34),(11,34),(8,30),(9,26),(16,27)], G)
poly(im, [(11,27),(8,24),(4,21),(3,18),(5,19),(8,21),(11,23),(15,24),(16,28)], G)
poly(im, [(10,29),(7,29),(4,33),(1,34),(0,38),(2,38),(3,36),(6,35),(9,33),(13,33)], G)
poly(im, [(10,32),(8,36),(5,38),(3,42),(1,42),(2,38),(5,35),(7,31)], G)
poly(im, [(13,32),(12,38),(9,40),(8,44),(6,44),(7,39),(9,36),(9,33)], G)
poly(im, [(16,31),(16,37),(14,40),(14,44),(12,43),(12,39),(13,35)], D)
rect(im, 7,27,7,2,H)
rect(im, 5,33,3,1,H)
rect(im, 8,33,2,2,K)
rect(im, 12,31,3,1,D)

# Right elbow projects out of its sleeve; long fingers curl downward.
poly(im, [(58,21),(63,24),(67,29),(65,37),(60,40),(56,36),(56,29)], S)
poly(im, [(59,23),(63,25),(64,29),(61,33),(57,31)], L)
poly(im, [(64,26),(67,25),(70,28),(72,34),(70,39),(72,42),
          (75,42),(77,45),(77,51),(75,50),(74,46),(71,45),
          (72,51),(71,56),(69,55),(69,49),(67,46),(67,53),
          (65,54),(65,47),(63,43),(63,39),(66,34),(65,30)], G)
poly(im, [(67,28),(69,29),(70,34),(68,39),(66,40),(65,39),(68,34)], D)
poly(im, [(65,40),(68,41),(70,44),(68,45),(66,43),(65,46)], D)
rect(im, 65,27,2,3,H)
rect(im, 71,43,2,1,H)
rect(im, 65,47,1,4,H)

# Bald green face flows into the long, bent elephant trunk.
poly(im, [(35,0),(43,0),(43,2),(47,2),(47,4),(50,4),(51,8),
          (51,17),(48,21),(45,25),(44,32),(44,37),(47,40),
          (51,39),(52,36),(52,33),(55,33),(56,37),(55,42),
          (52,46),(47,48),(41,47),(36,43),(33,38),(32,33),
          (32,22),(30,18),(30,8),(32,4),(35,4)], G)
poly(im, [(47,8),(50,9),(50,16),(47,21),(43,26),(42,34),
          (43,40),(47,43),(51,42),(54,38),(54,35),(55,38),
          (53,43),(49,46),(44,45),(39,42),(37,38),(37,31),
          (39,23),(43,20),(46,15)], D)
poly(im, [(34,5),(37,3),(41,3),(41,5),(35,6),(33,10),(32,10),(32,7)], H)
rect(im, 33,14,2,1,H)
poly(im, [(33,22),(35,23),(35,32),(36,35),(34,35),(33,31)], H)
# The two eyes are single, solid 2-pixel marks.
rect(im, 31,11,2,1,K)
rect(im, 46,10,2,1,K)
# Trunk creases and its small open tip.
rect(im, 34,26,3,1,D)
rect(im, 34,31,3,1,D)
rect(im, 36,37,3,1,K)
rect(im, 39,41,3,1,K)
rect(im, 47,43,3,1,K)
rect(im, 52,34,2,2,K)

# Small folded edges at the cowl, cuffs and hem break the broad cloth planes.
poly(im, [(23,17),(26,14),(28,14),(26,17),(24,18)], L)
rect(im, 23,20,2,1,L)
rect(im, 27,19,2,1,R)
rect(im, 49,17,2,1,L)
rect(im, 51,15,2,1,R)
rect(im, 55,19,2,2,S)
rect(im, 57,22,2,1,R)
poly(im, [(20,26),(20,29),(18,31),(16,31),(18,29),(18,26)], L)
rect(im, 17,34,2,2,L)
rect(im, 15,33,1,2,K)
rect(im, 21,32,1,2,K)
rect(im, 60,26,2,2,R)
rect(im, 58,29,2,1,S)
rect(im, 60,33,2,2,R)
rect(im, 58,35,1,2,L)
rect(im, 62,35,1,2,K)

# A few angular, worn cloth repairs, with the seams visible at game size.
poly(im, [(28,40),(31,39),(32,42),(31,47),(28,48),(27,45)], S)
rect(im, 28,41,2,1,L)
rect(im, 29,46,2,1,K)
rect(im, 27,43,1,2,K)
rect(im, 31,43,1,2,R)
poly(im, [(48,51),(51,50),(53,53),(52,57),(49,58),(48,55)], R)
rect(im, 49,52,2,1,L)
rect(im, 50,56,2,1,K)
rect(im, 52,54,1,1,L)

# Short crease facets follow the cloth's weight, rather than a repeated texture.
poly(im, [(26,50),(27,50),(26,55),(24,58),(24,55)], R)
poly(im, [(22,59),(23,59),(22,63),(20,65),(21,61)], R)
rect(im, 20,68,2,1,L)
poly(im, [(30,54),(31,51),(32,51),(31,56),(29,59)], L)
rect(im, 28,61,2,2,R)
rect(im, 28,65,1,2,K)
poly(im, [(35,46),(36,47),(34,51),(33,51)], L)
poly(im, [(39,50),(41,49),(40,54),(39,57),(38,57)], R)
rect(im, 38,60,1,3,L)
rect(im, 40,65,1,2,R)
poly(im, [(44,46),(46,48),(46,51),(44,50),(43,48)], R)
rect(im, 44,55,1,3,L)
rect(im, 48,61,2,1,R)
poly(im, [(56,46),(57,48),(58,52),(57,53),(55,49)], R)
rect(im, 57,56,2,2,L)
poly(im, [(59,60),(60,61),(61,65),(59,64)], R)
rect(im, 61,68,2,1,L)
rect(im, 54,62,1,3,K)
rect(im, 52,66,2,2,R)
rect(im, 55,70,2,1,L)
rect(im, 33,71,2,2,R)
rect(im, 36,74,2,1,S)
rect(im, 44,73,2,1,L)
rect(im, 49,75,2,2,R)
rect(im, 22,74,2,1,L)
rect(im, 59,74,2,1,R)

# Joint creases, knuckles, and the trunk's broad transverse wrinkles.
rect(im, 9,25,2,1,D)
rect(im, 4,35,2,1,D)
rect(im, 8,38,1,2,H)
rect(im, 13,36,1,2,G)
rect(im, 67,31,1,2,H)
rect(im, 67,36,2,1,K)
rect(im, 65,41,2,1,H)
rect(im, 71,46,1,2,D)
rect(im, 75,46,1,2,D)
rect(im, 36,19,3,1,D)
rect(im, 39,22,2,1,G)
rect(im, 37,28,2,1,G)
rect(im, 37,33,2,1,G)
rect(im, 39,38,2,1,G)
rect(im, 44,42,2,1,G)
rect(im, 48,45,2,1,G)

# Visible stitches fasten the two cloth repairs, and tears interrupt the hem.
rect(im, 27,40,1,1,L)
rect(im, 31,40,1,1,L)
rect(im, 26,44,2,1,L)
rect(im, 29,48,2,1,L)
rect(im, 32,45,1,1,L)
rect(im, 48,51,1,1,L)
rect(im, 52,51,1,1,L)
rect(im, 47,54,2,1,L)
rect(im, 53,56,1,1,L)
rect(im, 49,58,2,1,L)
rect(im, 18,71,2,1,R)
rect(im, 24,76,2,1,S)
rect(im, 35,76,1,2,K)
rect(im, 44,76,1,2,K)
rect(im, 53,76,2,1,L)
rect(im, 65,74,1,2,K)
# Creases above the knuckles and on the bald forehead remain separate from eyes.
rect(im, 5,23,2,1,D)
rect(im, 10,29,2,1,D)
rect(im, 3,37,1,1,H)
rect(im, 10,40,1,1,H)
rect(im, 66,44,1,1,H)
rect(im, 70,50,1,1,H)
rect(im, 42,5,3,1,D)
rect(im, 34,8,2,1,G)
rect(im, 45,15,2,1,G)
rect(im, 33,18,2,1,D)
rect(im, 41,30,1,2,G)
rect(im, 25,16,1,1,R)
rect(im, 54,21,1,1,L)
rect(im, 20,28,1,1,R)
rect(im, 61,30,1,1,L)
rect(im, 31,68,1,1,L)

# Cloth is visible inside the cowl and beside the underarm crease.
rect(im, 26,23,3,1,S)
rect(im, 24,34,1,2,R)
rect(im, 29,15,1,2,L)
rect(im, 47,20,1,1,R)
rect(im, 23,29,1,1,L)

# The rolled cowl seam and reinforced cuffs have short, visible stitches.
rect(im, 24,21,1,1,L)
rect(im, 28,22,1,1,L)
rect(im, 53,18,1,1,R)
rect(im, 48,23,1,1,L)
rect(im, 51,24,1,1,L)
rect(im, 17,28,1,1,L)
rect(im, 19,33,1,1,L)
rect(im, 57,32,1,1,L)
rect(im, 63,31,1,1,R)
rect(im, 59,37,1,1,L)
# A folded cheek, bent finger joints, and a frayed tear at either side.
poly(im, [(34,16),(36,16),(37,18),(35,18)], D)
rect(im, 10,35,1,1,H)
rect(im, 73,43,1,1,D)
rect(im, 64,43,1,1,D)
rect(im, 23,61,1,2,K)
rect(im, 24,63,1,1,L)
rect(im, 60,61,1,2,L)
rect(im, 58,64,1,1,K)

# Final broken crease facets articulate the remaining broad cloth panels.
rect(im, 27,37,2,1,L)
rect(im, 30,35,1,2,S)
rect(im, 31,50,1,1,R)
rect(im, 36,55,1,2,R)
rect(im, 38,69,1,2,L)
rect(im, 43,59,1,2,R)
rect(im, 47,48,1,2,L)
rect(im, 50,45,1,1,L)
rect(im, 53,60,1,1,R)
rect(im, 57,59,1,1,R)
rect(im, 25,69,1,1,L)
rect(im, 60,70,1,1,R)

# Give every edge a visible cloth fill before the single outer outline is added.
src = im.copy()
for y in range(im.height):
    for x in range(im.width):
        if src.getpixel((x,y)) == BLACK and any(
            not (0 <= x+dx < im.width and 0 <= y+dy < im.height)
            or src.getpixel((x+dx,y+dy))[3] == 0
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))):
            dot(im,x,y,S)

im = outline(im)
save(im)
