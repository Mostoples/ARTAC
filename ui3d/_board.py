from PIL import Image
names = "boot home alarm face ppg dispense done refill missed settings".split()
W, H = 640, 480
sh = Image.new('RGB', (5 * (W + 20) + 20, 2 * (H + 20) + 20), (233, 239, 247))
for i, n in enumerate(names):
    im = Image.open(f'layar/{n}@3x.png').convert('RGB').resize((W, H), Image.LANCZOS)
    sh.paste(im, (20 + (i % 5) * (W + 20), 20 + (i // 5) * (H + 20)))
sh.save('layar/_semua_layar.jpg', quality=88)
