from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image, ImageOps, ImageDraw

root = Path(__file__).resolve().parent / 'qa'
for file in root.glob('*.pdf'):
    pdf = pdfium.PdfDocument(str(file))
    pages=[]
    for i in range(len(pdf)):
        page=pdf[i]
        textpage=page.get_textpage()
        text=textpage.get_text_range()
        print(file.stem, i+1, len(text.split()), repr(text[:85]))
        im=page.render(scale=1.5).to_pil()
        im.save(root / f'{file.stem}_page_{i+1}.png')
        thumb=ImageOps.contain(im,(510,660))
        panel=Image.new('RGB',(530,700),'#ddd')
        panel.paste(thumb,((530-thumb.width)//2,25))
        ImageDraw.Draw(panel).text((10,680),f'Page {i+1}',fill='black')
        pages.append(panel)
    sheet=Image.new('RGB',(530*len(pages),700),'white')
    for i, im in enumerate(pages): sheet.paste(im,(530*i,0))
    sheet.save(root / f'{file.stem}_overview.png')
