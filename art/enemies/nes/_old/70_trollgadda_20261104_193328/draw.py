from pix import *

PAL = {
    'W': '4edc4a',  # willow light
    'V': '00a800',  # willow mid
    'g': '4fa667',  # hide
    'h': '2c6c44',  # hide shade, scale arcs, willow shade
    'c': 'e8e0c0',  # belly and tooth
    'b': '815423',  # wood and fin
    'B': '583518',  # wood shade
}

im = grid([
    '.........WWW.WWW....',
    '.......WWWWWWWWWWW..',
    '......WWVVWWWVVWWWW.',
    '......VVVVhVVVVhVVV.',
    '......hVhVVbBVhVhVh.',
    '......h...hbBh......',
    'b.......gggbBgggg...',
    'bb..gggghggbBKgggg..',
    '.bbbghhhghhhgKggKKg.',
    '.bbbgghggghgggKggggg',
    'bB..hhghhhghhKggKcKK',
    'B....ccccccccccccccc',
    '.......bb..ccccc....',
], PAL)

im = outline(im)
save(im)
