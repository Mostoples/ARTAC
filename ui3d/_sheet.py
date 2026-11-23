from PIL import Image
import glob, os
fs = sorted(glob.glob('ikon/*.png')); cols = 5
sh = Image.new('RGB', (cols * 200, 2 * 210), (233, 239, 247))
for i, f in enumerate(fs):
    im = Image.open(f).convert('RGBA').resize((190, 190))
    sh.paste(im, ((i % cols) * 200 + 5, (i // cols) * 210 + 10), im)
sh.save('_ikon_sheet.jpg', quality=90)
print(len(fs), [os.path.basename(f) for f in fs])
