from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

OUT = Path(__file__).parent
W, H, S = 720, 640, 2
OUTPUT_SIZE = (1920, 1080)
BACKGROUND = '#18191d'
TEXT = '#f4e8dd'
ORANGE = '#d97757'
INK = '#422e28'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def frame(i):
    phase = i / 48
    lift = math.sin(math.pi * phase) ** 2
    im = Image.new('RGB', (W*S, H*S), BACKGROUND)
    d = ImageDraw.Draw(im)
    def box(coords, fill, radius=0, outline=None, width=1):
        coords = tuple(round(v*S) for v in coords)
        if radius:
            d.rounded_rectangle(coords, radius=radius*S, fill=fill, outline=outline, width=width*S)
        else:
            d.ellipse(coords, fill=fill, outline=outline, width=width*S)
    def line(points, fill, width):
        pts = [(round(x*S),round(y*S)) for x,y in points]
        d.line(pts, fill=fill, width=round(width*S), joint='curve')
        r = width / 2
        for x,y in (points[0], points[-1]):
            box((x-r,y-r,x+r,y+r),fill)
    def text(y, value, size, color, bold=False):
        font = ImageFont.truetype(BOLD if bold else FONT, size*S)
        d.text((W*S/2,y*S), value, font=font, fill=color, anchor='mt')
    text(38, 'MY FUNPAY PROFILE', 14, '#c9afa0', True)
    box((51,78,669,143),'#101114',24)
    box((51,74,669,139),'#27282e',24, '#454047')
    text(96, 'funpay.com/users/8009331/', 28, TEXT, True)
    text(165, 'A little jump. A lot of joy.', 18, '#b7aaa2')

    # The shadow stays on the floor as the mascot rises.
    shadow_w = 104-39*lift
    box((360-shadow_w,532-8*(1-lift),360+shadow_w,546), '#121316')
    box((360-shadow_w*.65,531,360+shadow_w*.65,541), '#0d0e10')
    cy = 425-123*lift
    sx = 1.06-.13*lift
    sy = .87+.18*lift
    rotation = .07*math.sin(2*math.pi*phase)
    def pt(x,y):
        x,y=x*sx,y*sy
        return (360+x*math.cos(rotation)-y*math.sin(rotation),cy+x*math.sin(rotation)+y*math.cos(rotation))
    def face_line(points,width=8):
        line([pt(x,y) for x,y in points], INK, width)

    # Uneven rays echo Claude's terracotta starburst silhouette.
    vertices=[]
    rays=12
    for j in range(rays):
        theta=-math.pi/2+j*math.tau/rays
        radius=[99,87,101,94,102,90,96,103,89,101,91,98][j]
        for delta,r in [(-.115,54),(-.075,radius),(.075,radius),(.115,54)]:
            vertices.append(pt(math.cos(theta+delta)*r,math.sin(theta+delta)*r))
    d.polygon([(int(x*S),int(y*S)) for x,y in vertices],fill=ORANGE)
    # Happy closed eyes and a wide smile.
    for ex in [-27,27]:
        face_line([(ex-10,0),(ex-6,-6),(ex,-9),(ex+6,-6),(ex+10,0)],5)
    cheeks=[(-43,13),(43,13)]
    for x,y in cheeks:
        px,py=pt(x,y)
        box((px-9,py-4,px+9,py+4),'#eea084')
    mouth=[pt(-18,17),pt(18,17),pt(15,28),pt(8,35),pt(0,37),pt(-8,35),pt(-15,28)]
    d.polygon([(round(x*S),round(y*S)) for x,y in mouth], fill=INK)
    tongue=[pt(-9,31),pt(0,28),pt(9,31),pt(5,35),pt(-5,35)]
    d.polygon([(round(x*S),round(y*S)) for x,y in tongue],fill='#f1b19a')

    # Sparkles expand and brighten near the top of the jump.
    for j,(x,y,size) in enumerate([(166,285,13),(552,272,16),(206,394,9),(520,398,10),(276,245,8),(462,229,7)]):
        twinkle=max(0,math.sin(math.pi*phase))*(.75+.25*math.sin(phase*math.tau+j))
        r=size*twinkle
        if r>1:
            y-=14*lift
            coords=[(x,y-r),(x+r*.28,y-r*.28),(x+r,y),(x+r*.28,y+r*.28),(x,y+r),(x-r*.28,y+r*.28),(x-r,y),(x-r*.28,y-r*.28)]
            d.polygon([(round(a*S),round(b*S)) for a,b in coords],fill='#efc477' if j%2 else '#efa181')
    text(585, 'See you on FunPay!', 19, '#c9afa0')
    content_width = round(W * OUTPUT_SIZE[1] / H)
    content = im.resize((content_width, OUTPUT_SIZE[1]), Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', OUTPUT_SIZE, BACKGROUND)
    canvas.paste(content, ((OUTPUT_SIZE[0] - content_width) // 2, 0))
    return canvas

frames=[frame(i) for i in range(48)]
# A shared palette keeps static text and the background stable across frames.
sample=Image.new('RGB',(OUTPUT_SIZE[0]*4,OUTPUT_SIZE[1]))
for j,k in enumerate([0,12,24,36]):
    sample.paste(frames[k],(j*OUTPUT_SIZE[0],0))
palette=sample.quantize(colors=128)
indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
path=OUT/'claude-funpay-dark-1920x1080.gif'
indexed[0].save(path,save_all=True,append_images=indexed[1:],duration=50,loop=0,optimize=True,disposal=1)
sample.resize((1920,270),Image.Resampling.LANCZOS).save(OUT/'review-dark-1080p.png')
with Image.open(path) as gif:
    assert gif.n_frames==48
    assert gif.size==OUTPUT_SIZE
    assert gif.info['loop']==0
    total=0
    for k in range(gif.n_frames):
        gif.seek(k)
        gif.load()
        total+=gif.info['duration']
        if k == 24:
            gif.convert('RGB').save(OUT/'verified-dark-1080p.png')
    print(f'Verified: {gif.n_frames} frames, {gif.size}, {total} ms, infinite loop, {path.stat().st_size:,} bytes')
